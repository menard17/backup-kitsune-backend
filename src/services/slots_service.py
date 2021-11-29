import uuid

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient


class SlotService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def _create_slot(self, role_id, start, end, status) -> DomainResource:
        """Returns tuple of Exception and Slot resource in bundle.

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str

        :rtype: Exception
        :rtype: Practitioner
        """
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
                ("status", status),
            ],
        )
        if slot_search.entry is not None:
            return Exception("the time is already booked"), None

        slot_jsondict = {
            "resourceType": "Slot",
            "schedule": {"reference": f"Schedule/{schedule.id}"},
            "status": status or "busy",
            "start": start,
            "end": end,
            "comment": "slot creation from backend",
        }
        slot = construct_fhir_element(slot_jsondict["resourceType"], slot_jsondict)
        return slot

    def create_slot_for_practitioner_role(
        self, role_id, start, end, status="busy"
    ) -> tuple[Exception, DomainResource]:
        """Returns tuple of Exception and Slot resource.
        Actual slot is not created in the service but constructing json for slot

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str

        :rtype: Exception
        :rtype: Practitioner
        """
        slot = self._create_slot(role_id, start, end, status)
        slot = self.resource_client.create_resource(slot)
        return None, slot

    def create_slot_bundle(
        self, role_id, start, end, slot_id, status="busy"
    ) -> tuple[Exception, DomainResource]:
        """Returns tuple of Exception and Slot resource in bundle.

        :param role_id: id of practitioner
        :type role_id: str
        :param start: start time of the search of slots and schedule. Use iso date format
        :type start: str
        :param end: end time of the search of slots and schedule. Use iso date format
        :type end: str
        :param status: default is busy. free or busy
        :type status: str
        :param slot_id: Id for the slot. This is used to reference before creating slot resource
        :type slot_id: str

        :rtype: Exception
        :rtype: Practitioner
        """
        slot = self._create_slot(role_id, start, end, status)
        slot = self.resource_client.get_post_bundle(slot, slot_id)
        return None, slot

    def free_slot(self, slot_id: uuid):
        """
        data: "slot": [{"reference": "Slot/bf929953-f4df-4b54-a928-2a1ab8d5d550"}]
        we always created one slot only on appointment. so we can hardcode to index 0.
        and split with "/" to get the slot id.
        """

        slot_response = self.resource_client.get_resource(slot_id, "Slot")
        slot_response.status = "free"
        slot = construct_fhir_element(slot_response.resource_type, slot_response)
        slot = self.resource_client.get_put_bundle(slot, slot_id)
        return None, slot
