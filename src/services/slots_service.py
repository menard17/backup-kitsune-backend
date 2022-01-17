import uuid
from typing import Tuple

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient


class SlotService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def _create_slot(
        self, role_id, start, end, status, comment
    ) -> tuple[Exception, DomainResource]:
        """Returns tuple of Exception and Slot resource in bundle.

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str

        :rtype: Exception
        :rtype: Practitioner
        """
        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", role_id),
                ("active", str(True)),  # assumes single active schedule at a time
            ],
        )

        if schedule_search.entry is None:
            return Exception("cannat find schedule"), None

        # check if any other slot started during the requested slot
        schedule = schedule_search.entry[0].resource
        slot_search = self.resource_client.search(
            "Slot",
            search=[
                ("schedule", schedule.id),
                ("start", "ge" + start),
                ("start", "lt" + end),
                ("status:not", "free"),
            ],
        )

        if slot_search.entry is not None:
            return Exception("the time is already booked"), None

        # TODO: add custom search parameter to fhir
        # check if any other slot cover the whole requested slot
        slot_search = self.resource_client.search(
            "Slot",
            search=[
                ("schedule", schedule.id),
                ("start", "lt" + start),
                ("end", "ge" + end),
                ("status:not", "free"),
            ],
        )

        if slot_search.entry is not None:
            return Exception("the time is already booked inside"), None

        # check if any other slot not ended during the requested slot
        slot_search = self.resource_client.search(
            "Slot",
            search=[
                ("schedule", schedule.id),
                ("end", "ge" + start),
                ("end", "lt" + end),
                ("status:not", "free"),
            ],
        )

        if slot_search.entry is not None:
            return Exception("the time is already booked end"), None

        slot_jsondict = {
            "resourceType": "Slot",
            "schedule": {"reference": f"Schedule/{schedule.id}"},
            "status": status or "busy",
            "start": start,
            "end": end,
            "comment": comment,
        }
        slot = construct_fhir_element(slot_jsondict["resourceType"], slot_jsondict)
        return None, slot

    def create_slot_for_practitioner_role(
        self, role_id, start, end, status="busy", comment="slot creation from backend"
    ) -> tuple[Exception, DomainResource]:
        """Returns tuple of Exception and Slot resource.
        Actual slot is not created in the service but constructing json for slot

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str

        :rtype: Exception
        :rtype: Practitioner
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.create_resource(slot)
        return err, slot

    def create_slot_bundle(
        self,
        role_id,
        start,
        end,
        slot_id,
        status="busy",
        comment="slot creation from backend",
    ) -> tuple[Exception, DomainResource]:
        """Returns tuple of Exception and Slot resource in bundle.

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str
        :param slot_id: Id for the slot. This is used to reference before creating slot resource
        :type slot_id: str

        :rtype: Exception
        :rtype: Practitioner
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.get_post_bundle(slot, slot_id)
        return err, slot

    def update_slot(
        self, slot_id: uuid, status: str
    ) -> Tuple[Exception, DomainResource]:
        """
        Update slot status. this method is idempotent.

        :param slot_id: id of slot
        :type slot_id: uuid
        :param status: status you want to update to. status can be either free or busy
        :type status: str

        :rtype: Exception
        :rtype: Slot
        """

        if not (status == "free" or status == "busy"):
            return Exception(f"Status can only be free or busy for now: {status}"), None

        slot_response = self.resource_client.get_resource(slot_id, "Slot")
        slot_response.status = status
        slot = construct_fhir_element(slot_response.resource_type, slot_response)
        slot = self.resource_client.get_put_bundle(slot, slot_id)
        return None, slot

    def get_slot(self, schedule_id, start) -> Tuple[Exception, DomainResource]:
        search_clause = [("schedule", schedule_id), ("start", start)]
        slot_response = self.resource_client.search("Slot", search_clause)
        return None, slot_response
