from typing import TypedDict

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode


class AvailableTime(TypedDict):
    ...


class PractitionerRoleService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_practitioner_role(
        self,
        identity: str,
        is_doctor: bool,
        start: str,
        end: str,
        practitioner_id: str,
        practitioner_name: str,
        zoom_id: str,
        zoom_password: str,
        available_time: dict,
    ):
        if bool(is_doctor):
            practitioner_code = SystemCode.practitioner_code("doctor")
        else:
            practitioner_code = SystemCode.practitioner_code("nurse")

        practitioner_role_jsondict = {
            "resourceType": "PractitionerRole",
            "active": True,
            "period": {"start": start, "end": end},
            "practitioner": {
                "reference": practitioner_id,
                "display": practitioner_name,
            },
            "code": [{"coding": [practitioner_code]}],
            "availableTime": available_time,
            "extension": [
                {"url": "zoom-id", "valueString": zoom_id},
                {"url": "zoom-passcode", "valueString": zoom_password},
            ],
        }

        practitioner_role = construct_fhir_element(
            "PractitionerRole", practitioner_role_jsondict
        )
        practitioner_role = self.resource_client.get_post_bundle(
            practitioner_role, identity
        )
        return None, practitioner_role
