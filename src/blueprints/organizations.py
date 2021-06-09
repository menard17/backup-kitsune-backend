from flask import Blueprint, request
from adapters.fhir_store import ResourceClient
from middleware import jwt_authenticated
from fhir.resources.organization import Organization
from fhir.resources.address import Address

organization_blueprint = Blueprint(
    "organizations", __name__, url_prefix="/organizations"
)


@organization_blueprint.route("/<organization_id>", methods=["GET"])
@jwt_authenticated
def get_organization(organization_id: str) -> dict:
    """Returns details of a organization. Organization can be clincs, hospitals, and etc.
    Have to get FHIR's UUID from UID bypass for test.

    :param organization_id: uuid for organization
    :type organization_id: str

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resource(organization_id, "Organization").dict()


@organization_blueprint.route("/", methods=["GET"])
@jwt_authenticated
def get_organizations() -> dict:
    """Returns details of all organizations.
    Have to get FHIR's UUID from UID bypass for test

    :rtype: Dictionary
    """
    resourse_client = ResourceClient()
    return resourse_client.get_resources("Organization").dict()


@organization_blueprint.route("/", methods=["POST"])
@jwt_authenticated
def create_organization() -> dict:
    """Returns details of a organization created.
    This creates a organization in fhir.
    This does not check if there is a duplicate.
    By default, address is set to Japan.

    Example:
        body: {"name": "example hospital"}

    rtype: Dictionary
    """
    resourse_client = ResourceClient()
    organization = Organization.parse_obj(request.get_json())
    organization.active = True
    organization.address = list()
    address = Address.construct()
    address.country = "Japan"
    organization.address.append(address)
    return resourse_client.create_resource(organization).dict()
