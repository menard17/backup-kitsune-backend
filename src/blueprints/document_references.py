import json
import re
from datetime import datetime, timezone

from fhir.resources.documentreference import DocumentReference
from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from utils import role_auth
from utils.datetime_encoder import datetime_encoder
from utils.middleware import jwt_authenticated

document_references_blueprint = Blueprint(
    "document_references", __name__, url_prefix="/document_references"
)


@document_references_blueprint.route("/", methods=["Get"])
@jwt_authenticated()
def search_document_reference():
    return DocumentReferenceController().search_document_reference(request)


@document_references_blueprint.route("/", methods=["Post"])
@jwt_authenticated()
def post_document_resource():
    return DocumentReferenceController().create_document_reference(request)


class DocumentReferenceController:
    def __init__(self, resource_client=None):
        self.resource_client = resource_client or ResourceClient()

    def create_document_reference(self, request):
        """ the function to create a new document reference.
            "subject" in the request body is required and will be used to check authorization.
            It must refer to an existing patient or practitioner or will an data conflict error will be thrown by fhir.

        :param request: the request for this operation
        :rtype: Response
        """

        document_reference = DocumentReference.parse_obj(request.get_json())

        subject = document_reference.subject
        if not subject:
            return Response(status=400, response="missing param: subject")

        document_type = document_reference.type.coding[0].code
        if not document_type:
            return Response(status=400, response="missing param: type")

        subject_match = re.search("(Patient|Practitioner)/(.*)", subject.reference)
        if not subject_match:
            return Response(
                status=400,
                response=r"invalid param: subject. The 'subject' parameter only accepts format 'Patient|Practitioner/{id}'",
            )

        role_type = subject_match.group(1)
        role_id = subject_match.group(2)

        claims_roles = role_auth.extract_roles(request.claims)
        if "Patient" in claims_roles and (
            role_type == "Practitioner" or claims_roles["Patient"]["id"] != role_id
        ):
            return Response(
                status=403,
                response="patient can only create document references for him/herself",
            )

        if (
            "Practitioner" in claims_roles
            and role_type == "Practitioner"
            and claims_roles["Practitioner"]["id"] != role_id
        ):
            return Response(
                status=403,
                response="practitioner can not create document references for another practitioner",
            )

        # Overwrite `date` property
        document_reference.date = datetime.now(timezone.utc)

        # get previously existing items to ensure only the newly added item will be active
        search_clause = []
        search_clause.append(("subject", subject.reference))
        search_clause.append(("type", document_type))
        search_clause.append(("status", "current"))
        existing = self.resource_client.search(
            "DocumentReference",
            search=search_clause,
        )

        document_reference = self.resource_client.create_resource(document_reference)

        # change status of previously existing items to "superseded"
        if existing.entry:
            for e in existing.entry:
                self.resource_client.patch_resource(
                    e.resource.id,
                    "DocumentReference",
                    [{"op": "add", "path": "/status", "value": "superseded"}]
                )

        return Response(status=201, response=document_reference.json())

    def search_document_reference(self, request):
        """ the function to search document references.
            "subject" in the request body is required and will be used to check authorization.
            It must refer to an existing patient or practitioner or will an data conflict error will be thrown by fhir.

        :param subject: subject of the document reference. can be a patient or a pratitioner.
        :param document_type: document type of the document reference.
        :param date: date of the document reference.
        :param count: page count of search result items. default value 10.

        :response:
        {
            "data": [
                {document reference object},
                {document reference object},
                ...
            ],
            "links": [
                {link for next page},
                {link for previous page},
                ...
            ]
        }
        """

        subject = request.args.get("subject")
        date = request.args.get("date")
        document_type = request.args.get("document_type")
        page_count = request.args.get("count")
        status = request.args.get("status")

        if not subject:
            return Response(status=400, response="missing param: subject")

        subject_match = re.search("(Patient|Practitioner)/(.*)", subject)
        if not subject_match:
            return Response(
                status=400,
                response=r"invalid param: subject. The 'subject' parameter only accepts format 'Patient|Practitioner/{id}'",
            )

        role_type = subject_match.group(1)
        role_id = subject_match.group(2)

        claims_roles = role_auth.extract_roles(request.claims)
        if "Patient" in claims_roles and (
            role_type == "Practitioner" or claims_roles["Patient"]["id"] != role_id
        ):
            return Response(
                status=403,
                response="patient can only search document references for him/herself",
            )

        search_clause = []

        search_clause.append(("subject", subject))

        if date:
            search_clause.append(("date", date))

        if document_type:
            search_clause.append(("type", document_type))

        if page_count:
            search_clause.append(("_count", page_count))
        else:
            search_clause.append(("_count", "10"))

        if not status:
            search_clause.append(("status", "current"))
        else:
            search_clause.append(("status", status))

        search_clause.append(("_sort", "-lastUpdated"))

        result = self.resource_client.search(
            "DocumentReference",
            search=search_clause,
        )

        if result.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )

        return Response(
            status=200,
            response=json.dumps(
                {
                    "data": [datetime_encoder(e.resource.json()) for e in result.entry],
                    "links": [datetime_encoder(link.json()) for link in result.link],
                },
                default=json_serial,
            ),
        )
