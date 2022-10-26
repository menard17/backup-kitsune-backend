from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient


class ScheduleService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_schedule(self, role_id, name, start, end):
        schedule_jsondict = {
            "resourceType": "Schedule",
            "active": True,
            "actor": [
                {
                    "reference": role_id,
                    "display": name,
                }
            ],
            "planningHorizon": {"start": start, "end": end},
            "comment": "auto generated schedule on practitioner role creation",
        }
        schedule = construct_fhir_element("Schedule", schedule_jsondict)
        schedule = self.resource_client.get_post_bundle(schedule)
        return None, schedule

    def get_active_schedules(self, role_id):
        search_clause = [
            ("actor", role_id),
            (
                "active",
                str(True),
            ),
        ]
        return self.resource_client.search("Schedule", search_clause)
