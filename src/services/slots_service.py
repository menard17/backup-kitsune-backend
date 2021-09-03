from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient


class SlotService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_slot_for_practitioner_role(
        self, role_id, start, end, status="busy"
    ) -> tuple[Exception, DomainResource]:
        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", role_id),
                ("active", str(True)),  # assumes single active schedule at a time
            ],
        )

        if schedule_search.entry is None:
            return Exception("cannat find schedule"), None

        # check if the time is available
        schedule = schedule_search.entry[0].resource
        slot_search = self.resource_client.search(
            "Slot",
            search=[
                ("schedule", schedule.id),
                ("start", "ge" + start),
                ("start", "lt" + end),
                ("status", "busy"),
            ],
        )
        if slot_search.entry is not None:
            return Exception("the time is already booked"), None

        slot_jsondict = {
            "resourceType": "Slot",
            "schedule": {"reference": "Schedule/" + schedule.id},
            "status": status or "busy",
            "start": start,
            "end": end,
            "comment": "slot creation from backend",
        }
        slot = construct_fhir_element("Slot", slot_jsondict)
        slot = self.resource_client.create_resource(slot)
        return None, slot
