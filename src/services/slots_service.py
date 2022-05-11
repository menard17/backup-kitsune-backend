import uuid

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource
from fhir.resources.slot import Slot

from adapters.fhir_store import ResourceClient


class SlotService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def _create_slot(
        self, role_id, start, end, status, comment
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

        :rtype: tuple[Exception, DomainResource]
        """
        schedule_search = self.resource_client.search(
            "Schedule",
            search=[
                ("actor", role_id),
                ("active", str(True)),  # assumes single active schedule at a time
            ],
        )

        if schedule_search.entry is None:
            return Exception("cannot find schedule"), None

        schedule = schedule_search.entry[0].resource

        additional_params = [("status:not", "free")]
        _, overlapped_not_free_slots = self.search_overlapped_slots(
            schedule.id, start, end, additional_params
        )
        if overlapped_not_free_slots:
            return Exception("the time is already booked"), None

        slot_jsondict = {
            "resourceType": "Slot",
            "schedule": {"reference": f"Schedule/{schedule.id}"},
            "status": status or "busy",
            "start": start,
            "end": end,
            "comment": comment,
        }
        slot = construct_fhir_element(slot_jsondict["resourceType"], slot_jsondict)
        return None, slot

    def create_slot_for_practitioner_role(
        self, role_id, start, end, status="busy", comment="slot creation from backend"
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

        :rtype: tuple[Exception, DomainResource]
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.create_resource(slot)
        return err, slot

    def create_slot_bundle(
        self,
        role_id,
        start,
        end,
        slot_id,
        status="busy",
        comment="slot creation from backend",
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

        :rtype: tuple[Exception, DomainResource]
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.get_post_bundle(slot, slot_id)
        return err, slot

    def update_slot(
        self, slot_id: uuid, status: str
    ) -> tuple[Exception, DomainResource]:
        """
        Update slot status. this method is idempotent.

        :param slot_id: id of slot
        :type slot_id: uuid
        :param status: status you want to update to. status can be either free or busy
        :type status: str

        :rtype: tuple[Exception, DomainResource]
        """

        if not (status == "free" or status == "busy"):
            return Exception(f"Status can only be free or busy for now: {status}"), None

        slot_response = self.resource_client.get_resource(slot_id, "Slot")
        slot_response.status = status
        slot = construct_fhir_element(slot_response.resource_type, slot_response)
        slot = self.resource_client.get_put_bundle(slot, slot_id)
        return None, slot

    def search_overlapped_slots(
        self,
        schedule_id: uuid,
        start: str,
        end: str,
        additional_params: list[tuple] = [],
    ) -> tuple[Exception, list[Slot]]:
        """
        Search overlapped slots based on specific parameters.

        This search will find any slots that have intersection with
        (start, end) interval, meaning it will exclude any slots that might just
        next to the interval, e.g. (_, start] or [end, _)

        Additional params (such as "status") can be provided as part of the
        search slots.

        :param schedule_id: id of schedule for this slot search
        :type schedule_id: uuid
        :param start: start time in ISO format
        :type start: str
        :param end: end time in ISO format
        :type end: str
        :param additional_params: additional search criteria
        :type additional_params: list[tuple]

        :rtype: tuple[Exception, list[Slot]]
        """
        # Find any slot that have slot.start < end and slot.end > start
        # See https://stackoverflow.com/questions/325933/determine-whether-two-date-ranges-overlap
        search_clause = [
            ("schedule", schedule_id),
            ("start", "lt" + end),
            ("end", "gt" + start),
        ] + additional_params
        slots = self._search_slots(search_clause)

        return None, slots

    def _search_slots(self, search_clause) -> list[DomainResource]:
        slots = []

        result = self.resource_client.search("Slot", search_clause)
        if result.entry is not None:
            for entry in result.entry:
                slots.append(entry.resource)

        return slots
