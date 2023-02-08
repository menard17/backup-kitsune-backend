import base64
import logging
import os
import re

from fhir.resources.bundle import Bundle
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from services.firestore_service import FireStoreService
from services.notion_service import NotionService

pubsub_blueprint = Blueprint("pubsub", __name__, url_prefix="/pubsub")

log = logging.getLogger(__name__)


# TODO: AB#1211, this flag is used to enable firestore as well.
IS_SYNCING_TO_NOTION_ENABLED = os.getenv("IS_SYNCING_TO_NOTION_ENABLED")


@pubsub_blueprint.route("/fhir", methods=["POST"])
def fhir() -> Response:
    return PubsubController().fhir(request)


class PubsubController:
    def __init__(
        self,
        resource_client: ResourceClient = None,
        notion_service: NotionService = None,
        is_syncing_to_notion_enabled: str = None,
        firestore_service: FireStoreService = None,
    ):
        self.resource_client = resource_client or ResourceClient()
        self.notion_service = notion_service or NotionService()
        self.is_syncing_to_notion_enabled = (
            is_syncing_to_notion_enabled or IS_SYNCING_TO_NOTION_ENABLED
        )
        self.firestore_service = firestore_service or FireStoreService()

    def fhir(self, request) -> Response:
        """Receive Pub/Sub message"""
        if (
            self.is_syncing_to_notion_enabled is None
            or self.is_syncing_to_notion_enabled == "false"
        ):
            msg = "Syncing to Notion is not enabled for FHIR pub/sub. Skipping the message."
            log.warning(f"warn: {msg}")
            return Response(status=204)

        envelope = request.get_json()
        log.info(f"Envelope: {envelope}")

        if not envelope:
            msg = "no Pub/Sub message received"
            log.error(f"error: {msg}")
            return Response(
                status=400, response=f"Bad Request: {msg}", mimetype="text/plain"
            )
        log.info(f"Envelope: {envelope}")

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format, no message field found"
            log.error(f"error: {msg}")
            return Response(
                status=400, response=f"Bad Request: {msg}", mimetype="text/plain"
            )

        pubsub_message = envelope["message"]
        log.info(f"Pub/Sub Message: {pubsub_message}")
        if (
            not isinstance(pubsub_message, dict)
            or "data" not in pubsub_message
            or "attributes" not in pubsub_message
        ):
            msg = "invalid Pub/Sub message format, no data/attributes field found"
            log.error(f"error: {msg}")
            return Response(
                status=400, response=f"Bad Request: {msg}", mimetype="text/plain"
            )

        attributes = pubsub_message["attributes"]
        action = attributes["action"]
        payload_type = attributes["payloadType"]
        resource_type = attributes["resourceType"]
        data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
        log.info(f"Data: {data}")
        resource_id = re.findall(rf".*\/fhir\/{resource_type}\/(.*)", data)[0]

        if (
            (
                resource_type == "Encounter"
                or resource_type == "DocumentReference"
                or resource_type == "MedicationRequest"
                or resource_type == "ServiceRequest"
            )
            and (action == "CreateResource" or action == "PatchResource")
            and payload_type == "NameOnly"
        ):
            return self._post_encounter(resource_id)

        msg = f"No operation for pubsub with the following input: [attributes={attributes}, data={data}]"
        log.warning(f"warn: {msg}")
        return Response(status=204)

    def _post_encounter(self, encounter_id: str) -> Response:
        encounter_search_clause = [
            ("_id", encounter_id),  # encounter
            ("_include", "Encounter:account"),  # account
            ("_include", "Encounter:appointment"),  # appointment
            ("_include", "Encounter:patient"),  # patient
            # Note that below return PractitionerRole instead of Practitioner
            # This is probably due to us using the PractitionerRole to link
            # with the Encounter instead of the Practitioner resource.
            ("_include", "Encounter:practitioner"),  # practitioner_role
            ("_revinclude", "DocumentReference:encounter"),  # clinical_note
            ("_revinclude", "MedicationRequest:encounter"),  # medication_request
            ("_revinclude", "ServiceRequest:encounter"),  # service_request
        ]
        encounter_bundle = self.resource_client.search(
            "Encounter", search=encounter_search_clause
        )

        # Currently there is no way to include the insurance card in encounter
        # search, so we have to make a separate one.
        patient = self._find_resource_in_bundle(encounter_bundle, "Patient")
        insurance_card_bundle = None
        medical_card_bundle = None
        if patient is not None:
            insurance_card_search_clause = [
                ("patient", patient.id),
                ("status", "current"),
                ("type", "64290-0"),  # Custom code for Insurance Card
            ]
            insurance_card_bundle = self.resource_client.search(
                "DocumentReference", search=insurance_card_search_clause
            )
            medical_card_search_clause = [
                ("patient", patient.id),
                ("status", "current"),
                ("type", "00001-1"),  # Custom code for Insurance Card
            ]
            medical_card_bundle = self.resource_client.search(
                "DocumentReference", search=medical_card_search_clause
            )

        encounter = self._find_resource_in_bundle(encounter_bundle, "Encounter")
        account = self._find_resource_in_bundle(encounter_bundle, "Account")
        appointment = self._find_resource_in_bundle(encounter_bundle, "Appointment")
        practitioner_role = self._find_resource_in_bundle(
            encounter_bundle, "PractitionerRole"
        )
        clinical_note = self._find_resource_in_bundle(
            encounter_bundle, "DocumentReference"
        )
        medication_request = self._find_resource_in_bundle(
            encounter_bundle, "MedicationRequest"
        )
        service_request = self._find_resource_in_bundle(
            encounter_bundle, "ServiceRequest"
        )
        insurance_card = self._find_resource_in_bundle(
            insurance_card_bundle, "DocumentReference"
        )
        medical_card = self._find_resource_in_bundle(
            medical_card_bundle, "DocumentReference"
        )

        notion_encounter_query_results = self.notion_service.query_encounter_page(
            encounter_id=encounter_id
        )
        if len(notion_encounter_query_results["results"]) == 0:
            encounter_page = self.notion_service.create_encounter_page(
                encounter_id=encounter_id
            )
        else:
            encounter_page = notion_encounter_query_results["results"][0]

        self.notion_service.sync_encounter_to_notion(
            encounter_page_id=encounter_page["id"],
            account=account,
            appointment=appointment,
            patient=patient,
            practitioner_role=practitioner_role,
            clinical_note=clinical_note,
            medication_request=medication_request,
            service_request=service_request,
            insurance_card=insurance_card,
            medical_card=medical_card,
        )

        self.firestore_service.sync_encounter_to_firestore(
            appointment=appointment,
            encounter=encounter,
            patient=patient,
            medication_request=medication_request,
            service_request=service_request,
        )

        return Response(
            status=200, response=encounter_page["id"], mimetype="text/plain"
        )

    def _find_resource_in_bundle(self, bundle: Bundle, fhir_type: str):
        if bundle is None or bundle.entry is None:
            return None
        result = [
            x.resource for x in bundle.entry if x.resource.resource_type == fhir_type
        ]
        resource = result[0] if len(result) > 0 else None
        return resource
