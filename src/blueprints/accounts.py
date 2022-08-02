import json

from flask import Blueprint, Response, request

from adapters.fhir_store import ResourceClient
from json_serialize import json_serial
from services.account_service import AccountService
from services.invoice_service import InvoiceService
from utils import role_auth
from utils.middleware import jwt_authenticated, jwt_authorized
from utils.string_manipulation import to_bool

account_blueprint = Blueprint("accounts", __name__, url_prefix="/accounts")


class AccountController:
    """
    Controller is the class that holds the functions for the calls of accounts blueprint.
    """

    def __init__(
        self, resource_client=None, account_service=None, invoice_service=None
    ):
        self.resource_client = resource_client or ResourceClient()
        self.account_service = account_service or AccountService(self.resource_client)
        self.invoice_service = invoice_service or InvoiceService(self.resource_client)

    def create_account(self, request) -> Response:
        """Returns created account"""
        request_body = request.get_json()
        patient_id = request_body.get("patient_id")
        description = request_body.get("description")
        err, account = self.account_service.create_account_resource(
            patient_id, description
        )
        if err is not None:
            return Response(status=400, response=err.args[0])
        return Response(status=201, response=account.json())

    def get_account(self, request, account_id: str) -> Response:
        """Returns details of an account.

        :param account_id: uuid for account
        :type account_id: str

        :rtype: Response
        """
        err, account = self.account_service.get_account(account_id)

        claims_roles = role_auth.extract_roles(request.claims)
        if not role_auth.is_authorized(
            claims_roles, "Staff", "*"
        ) or not role_auth.is_authorized(
            claims_roles, "Patient", account.subject.reference
        ):
            Response(status=401, response="User not authorized to perform given action")

        if err is not None:
            return Response(status=400, response=err.args[0])
        return Response(status=200, response=json.dumps({"data": account.json()}))

    def inactivate_account(self, account_id) -> Response:
        """
        This is idempotent operation that inactivate account.
        """
        err, _ = self.account_service.inactivate_account(account_id)
        if err is not None:
            return Response(status=400, response=err.args[0])
        return Response(status=204)

    def get_invoice_by_account_id(self, account_id: str):
        err, invoice = self.invoice_service.get_invoice_by_account_id(account_id)
        if err is not None:
            return Response(status=400, response=err.args[0])

        if invoice.entry is None:
            return Response(
                status=200, response=json.dumps({"data": []}, default=json_serial)
            )
        return Response(
            status=200,
            response=json.dumps(
                {"data": [e.resource.json() for e in invoice.entry]},
                default=json_serial,
            ),
        )

    def search(self) -> Response:
        """Returns list of account matching searching query

        :returns: Json list of appointments
        :rtype: Response
        """
        patient_id = request.args.get("patient_id")
        status = request.args.get("status")
        include_invoice = to_bool(request.args.get("include_invoice"))
        search_clause = []

        if include_invoice:
            search_clause.append(("_revinclude:iterate", "Invoice:account"))
        if patient_id:
            search_clause.append(("patient", patient_id))
        if status:
            search_clause.append(("status", status))

        result = self.resource_client.search(
            "Account",
            search=search_clause,
        )
        if result.total == 0:
            return Response(status=200, response=json.dumps([]))
        resp = json.dumps(
            [json.loads(e.resource.json()) for e in result.entry],
            default=json_serial,
        )
        return Response(status=200, response=resp)


@account_blueprint.route("/<account_id>", methods=["GET"])
@jwt_authenticated()
def get_account(account_id: str):
    """
    Authorization added in AccountController.get_account
    """
    return AccountController().get_account(request, account_id)


# TODO: AB#812
@account_blueprint.route("/<account_id>", methods=["DELETE"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def cancel_account(account_id: str):
    return AccountController().inactivate_account(account_id=account_id)


# TODO: AB#812
@account_blueprint.route("/<account_id>/invoices", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Patient/*")
def get_account_invoice(account_id: str):
    return AccountController().get_invoice_by_account_id(account_id=account_id)


@account_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
@jwt_authenticated("/Practitioner/*")
def create_account():
    return AccountController().create_account(request)


@account_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
@jwt_authorized("/Practitioner/*")
def get_accounts():
    return AccountController().search()
