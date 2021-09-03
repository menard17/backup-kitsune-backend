from fhir.resources.address import Address
from fhir.resources.organization import Organization
from flask import Blueprint, request
from flask.wrappers import Response

from adapters.fhir_store import ResourceClient
from utils.middleware import jwt_authenticated

organization_blueprint = Blueprint(
    "organizations", __name__, url_prefix="/organizations"
)


@organization_blueprint.route("/<organization_id>", methods=["GET"])
@jwt_authenticated()
def get_organization(organization_id: str) -> dict:
    """Returns details of an organization. Organization can be clincs,
    hospitals, and etc. Have to get FHIR's UUID from UID bypass for test.

    :param organization_id: uuid for organization
    :type organization_id: str

    :rtype: dict
    """
    return _get_organization(organization_id).dict()


def _get_organization(organization_id: str) -> Organization:
    resourse_client = ResourceClient()
    return resourse_client.get_resource(organization_id, "Organization")


@organization_blueprint.route("/", methods=["GET"])
@jwt_authenticated()
def get_organizations() -> dict:
    """Returns details of all organizations.
    Have to get FHIR's UUID from UID bypass for test

    :rtype: dict
    """
    resourse_client = ResourceClient()
    if name := request.args.get("name"):
        response = resourse_client.get_resources_by_key(
            "name", name, "Organization"
        ).dict()
        if response.get("total") > 0:
            return {k: v for (k, v) in response.items() if k == "entry"}

        return {"entry": []}
    return resourse_client.get_resources("Organization").dict()


@organization_blueprint.route("/", methods=["POST"])
@jwt_authenticated()
def create_organization() -> dict:
    """Returns details of a organization created.
    This creates a organization in fhir.
    This does not check if there is a duplicate.
    By default, address is set to Japan.

    Example:
        body: {"name": "example hospital"}

    rtype: dict
    """
    resourse_client = ResourceClient()
    body = request.get_json()
    if name := body.get("name"):
        org_list = resourse_client.get_resources_by_key(
            "name", name, "Organization"
        ).dict()
        if org_list.get("total") > 0:
            return Response(status=400, response="Organization already exists")
        address = Address.construct()
        address.country = "Japan"
        organization = Organization.parse_obj(body)
        organization.active = True
        organization.address = [address]
        return resourse_client.create_resource(organization).dict()
    return Response(status=400, response="Body should contain name")
