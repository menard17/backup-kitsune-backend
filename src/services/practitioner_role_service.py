import json
import uuid
import pandas as pd
from typing import Dict, List, Optional, Set, Tuple, TypedDict

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from datetime import datetime
from adapters.fhir_store import ResourceClient
from utils.system_code import ServiceURL, SystemCode


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
        visit_type: str = "",
        available_time: Optional[dict] = None,
    ):
        practitioner_code = SystemCode.practitioner_code(role_type)
        code = [{"coding": [practitioner_code]}]

        # visit type to differentiate doctors for appointments and lineup (walk-in)
        if visit_type:
            visit_type_code = SystemCode.visit_type_code(visit_type)
            code.append({"coding": [visit_type_code]})

        practitioner_role_jsondict = {
            "resourceType": "PractitionerRole",
            "active": True,
            "period": {"start": start, "end": end},
            "practitioner": {
                "reference": practitioner_id,
                "display": practitioner_name,
            },
            "code": code,
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
        start: Optional[str] = None,
        end: Optional[str] = None,
        available_time: Optional[list] = None,
        visit_type: str = "",
    ):
        modified = False
        if start:
            modified = True
            practitioner_role.period.start = start
        if end:
            modified = True
            practitioner_role.period.end = end
        if available_time is not None:
            modified = True
            if not available_time:
                practitioner_role.availableTime = [{}]
            else:
                practitioner_role.availableTime = list(filter(None, available_time))

        if visit_type:
            modified = True
            codes = practitioner_role.code or []

            # check that only doctor can update visit type
            if not any(
                [
                    c.coding[0].system == ServiceURL.practitioner_type
                    and c.coding[0].code == "doctor"
                    for c in codes
                ]
            ):
                return Exception("Can only update visit type for doctor"), None

            # find the code and override with the new visit type
            # otherwise append with the new code if visit type code not exist already.
            found_idx = None
            new_code = SystemCode.visit_type_code(visit_type)
            new_code = construct_fhir_element("CodeableConcept", {"coding": [new_code]})
            for idx, code in enumerate(codes):
                if code.coding[0].system == ServiceURL.practitioner_visit_type:
                    found_idx = idx

            if found_idx:
                practitioner_role.code[found_idx] = new_code
            else:
                practitioner_role.code.append(new_code)

        if modified:
            practitioner_role_bundle = self.resource_client.get_put_bundle(
                practitioner_role, practitioner_role.id
            )
            return None, practitioner_role_bundle
        return None, None

    def get_practitioner_ids(
        self, role_type: str
    ) -> Tuple[Optional[Exception], Optional[Set[str]]]:
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

    def schedule_is_available_for_doctor(self, role_id: uuid, startTime: datetime, endTime: datetime):
        search_clause = [
            ("_id", role_id),
            ("active", str(True)),
            ("coding", "walk-in"),
        ]
        practitioner_role = self.resource_client.search("PractitionerRole", search_clause)
        practitioner_role_json = json.loads(practitioner_role.json())
        available_time = practitioner_role_json["entry"][0]["resource"]["availableTime"]
        available_time_start = datetime.strftime(pd.to_datetime(available_time[0]['availableStartTime']), "%H:%M:00")
        available_time_end = datetime.strftime(pd.to_datetime(available_time[0]['availableEndTime']), "%H:%M:00")
        startTime_str = startTime.strftime("%H:%M:00")
        endTime_str = endTime.strftime("%H:%M:00")
        return (available_time_start <= startTime_str and available_time_end >= startTime_str and
                available_time_start <= endTime_str and available_time_end >= endTime_str)
