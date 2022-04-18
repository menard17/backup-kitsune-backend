import uuid
from typing import Dict, List, Set, Tuple, TypedDict

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

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
        role_type: str,
        start: str,
        end: str,
        practitioner_id: str,
        practitioner_name: str,
        zoom_id: str = None,
        zoom_password: str = None,
        available_time: dict = None,
    ):
        practitioner_code = SystemCode.practitioner_code(role_type)

        practitioner_role_jsondict = {
            "resourceType": "PractitionerRole",
            "active": True,
            "period": {"start": start, "end": end},
            "practitioner": {
                "reference": practitioner_id,
                "display": practitioner_name,
            },
            "code": [{"coding": [practitioner_code]}],
        }

        if available_time is not None:
            if not available_time:
                practitioner_role_jsondict["availableTime"] = [{}]
            else:
                practitioner_role_jsondict["availableTime"] = available_time
        elif role_type != "doctor":
            # Hard coded for all days for nurse for now
            practitioner_role_jsondict["availableTime"] = [
                {
                    "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
                    "availableStartTime": "00:00:00",
                    "availableEndTime": "23:59:59",
                },
            ]
        if zoom_id and zoom_password:
            practitioner_role_jsondict["extension"] = [
                {"url": "zoom-id", "valueString": zoom_id},
                {"url": "zoom-passcode", "valueString": zoom_password},
            ]

        practitioner_role = construct_fhir_element(
            "PractitionerRole", practitioner_role_jsondict
        )

        practitioner_role = self.resource_client.get_post_bundle(
            practitioner_role, identity
        )
        return None, practitioner_role

    def update_practitioner_role(
        self,
        practitioner_role: DomainResource,
        start: str = None,
        end: str = None,
        zoom_id: str = None,
        zoom_password: str = None,
        available_time: list = None,
    ):
        modified = False
        if start and end:
            modified = True
            practitioner_role.period = {"start": start, "end": end}
        if available_time is not None:
            modified = True
            if not available_time:
                practitioner_role.availableTime = [{}]
            else:
                practitioner_role.availableTime = list(filter(None, available_time))
        if zoom_id and zoom_password:
            modified = True
            practitioner_role.extension = [
                {"url": "zoom-id", "valueString": zoom_id},
                {"url": "zoom-passcode", "valueString": zoom_password},
            ]
        if modified:
            practitioner_role_bundle = self.resource_client.get_put_bundle(
                practitioner_role, practitioner_role.id
            )
            return None, practitioner_role_bundle
        return None, None

    def get_practitioner_ids(self, role_type: str) -> Tuple[Exception, Set[str]]:
        """Returns list of practitioner ids referenced by practitioner role with given role type

        :param role_type: doctor or nurse
        :type role_type: str

        :rtype: Tuple[Exception, Set[str]]
        """
        if role_type != "doctor" and role_type != "nurse":
            return Exception(f"Not implemented role is provided: {role_type}"), None

        role_search_clause = []
        role_search_clause.append(("role", role_type))
        practitioner_roles = self.resource_client.search(
            "PractitionerRole", role_search_clause
        )
        if practitioner_roles.total == 0:
            return None, set()

        practitioner_ids = set()
        for role in practitioner_roles.entry:
            practitioner_ids.add(role.resource.practitioner.reference.split("/")[1])
        return None, practitioner_ids

    def get_practitioner_name(self, loc: str, role_id: uuid) -> Tuple[Exception, Dict]:
        """Returns dictionary of practitioner name based on loc.

        If loc is not found, loc=ABC is returned. If loc=ABC is not found, NONE is returned.

        :param loc: ABC, IDE, etc
        :type loc: str

        :rtype: Tuple[Exception, Dict]
        """
        practitioner_role = self.resource_client.get_resource(
            role_id, "PractitionerRole"
        )
        practitioner_id = practitioner_role.practitioner.reference.split("/")[1]
        practitioner = self.resource_client.get_resource(
            practitioner_id, "Practitioner"
        )
        practitioner_name_list: List[DomainResource] = list(
            filter(lambda x: x.extension[0].valueString == loc, practitioner.name)
        )
        if practitioner_name_list:
            return None, practitioner_name_list[0].dict()
        else:
            practitioner_name_list: List[DomainResource] = list(
                filter(lambda x: x.extension[0].valueString == "ABC", practitioner.name)
            )
            if practitioner_name_list:
                return None, practitioner_name_list[0].dict()
        return Exception("No item found"), None
