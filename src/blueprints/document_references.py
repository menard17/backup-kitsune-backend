import json
import re

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.document_reference_service import DocumentReferenceService
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
    def __init__(self, resource_client=None, document_reference_service=None):
        self.resource_client = resource_client or ResourceClient()
        self.document_reference_service = (
            document_reference_service or DocumentReferenceService(self.resource_client)
        )

    def create_document_reference(self, request):
        """the function to create a new document reference.
            "subject" in the request body is required and will be used to check authorization.
            It must refer to an existing patient or practitioner or will an data conflict error will be thrown by fhir.

        :param request: the request for this operation
        {
            "subject": "Patient/c696cd08-babf-4ec2-8b40-73ffd422d571",
            "document_type": "insurance_card",
            "pages": [
                {
                    "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
                    "title": "Page 1"
                },
                {
                    "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
                    "title": "Page 2"
                },
                {
                    "url": "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
                    "title": "Page 3"
                }
            ]
        }
        :rtype: Response
        """
        request_body = request.get_json()

        subject = request_body.get("subject")
        if not subject:
            return Response(status=400, response="missing param: subject")

        document_type = request_body.get("document_type")
        if not document_type:
            return Response(status=400, response="missing param: document_type")

        pages = request_body.get("pages")
        if len(pages) == 0:
            return Response(status=400, response="at least one page should be added")

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

        document_reference = self.document_reference_service.create_document_reference(
            subject, document_type, pages
        )
        return Response(status=201, response=document_reference.json())

    def search_document_reference(self, request):
        """the function to search document references.
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

        result = self.document_reference_service.search_document_reference(
            subject, date, document_type, page_count, status
        )

        if result.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )

        return Response(
            status=200,
            response=json.dumps(
                {"data": [datetime_encoder(e.resource.dict()) for e in result.entry]},
                default=json_serial,
            ),
        )
