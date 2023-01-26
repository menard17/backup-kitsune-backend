from datetime import datetime, time, timedelta
from uuid import UUID, uuid1

import pytz
from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource
from fhir.resources.practitionerrole import PractitionerRoleAvailableTime
from fhir.resources.slot import Slot

from adapters.fhir_store import ResourceClient

# The default duration for a single appointment
DEFAULT_SLOT_DURATION = timedelta(minutes=10)
# The default delta for rounding up time, for example 15 minutes mean
# 12:05 -> 12:15
DEFAULT_ROUND_UP_DELTA = timedelta(minutes=10)


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

        :rtype: tuple
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

        :rtype: tuple
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.create_resource(slot)
        return err, slot

    def create_slot_bundle(
        self,
        role_id,
        start: str,
        end: str,
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

        :rtype: tuple
        """
        err, slot = self._create_slot(role_id, start, end, status, comment)
        if err is None:
            slot = self.resource_client.get_post_bundle(slot, slot_id)
        return err, slot

    def update_slot(
        self, slot_id: UUID, status: str
    ) -> tuple[Exception, DomainResource]:
        """
        Update slot status. this method is idempotent.

        :param slot_id: id of slot
        :type slot_id: UUID
        :param status: status you want to update to. status can be either free or busy
        :type status: str

        :rtype: tuple
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
        schedule_id: UUID,
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
        :type schedule_id: UUID
        :param start: start time in ISO format
        :type start: str
        :param end: end time in ISO format
        :type end: str
        :param additional_params: additional search criteria
        :type additional_params: list[tuple]

        :rtype: tuple
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

    def generate_available_slots(
        self,
        schedule_id: str,
        start_time: datetime,
        end_time: datetime,
        available_time: list[PractitionerRoleAvailableTime],
        busy_slots: list[Slot],
        timezone: pytz.timezone,
        duration: timedelta = DEFAULT_SLOT_DURATION,
        round_up_delta: timedelta = DEFAULT_ROUND_UP_DELTA,
    ) -> tuple[Exception, list[Slot]]:
        """
        Generate a list of available/free slots.

        The main purpose is to generate a list of available slots on the
        frontend so that booking can be done.

        The correct way should be pre-generate these slots, but that might
        require a scheduling system, so we just create these for now.

        This is assuming that the busy slots are not overlapped. Otherwise this
        function will not generate correctly.

        Note that this will just create arbitrary slots, and nothing will
        be committed to FHIR.

        DO NOT USE THE IDS IN ANY CIRCUMSTANCES, as they are just mocked and
        might mess up with linking resources since these are no real FHIR.

        :param schedule_id: id of schedule for this slot search
        :type schedule_id: UUID
        :param start_time: start time as datetime object
        :type start_time: datetime
        :param end_time: end time as datetime object
        :type end_time: datetime
        :param available_time: list of availabilities from PractitionerRole
        :type available_time: list[PractitionerRoleAvailableTime]
        :param timezone: the timezone for checking availability
        :type timezone: timezone
        :param duration: the duration for a slot
        :type duration: timedelta
        :param round_up_delta: the rounding of time, e.g. 15 mins is 12:04 -> 12:15
        :type round_up_delta: timedelta

        :rtype: tuple
        """
        slots = []

        slot_start = self._ceil_time(start_time, round_up_delta)
        while slot_start + duration <= end_time:
            slot_end = slot_start + duration

            if self._does_slot_time_inside_availability(
                slot_start, slot_end, timezone, available_time
            ) and not self._does_slot_time_overlap_with_busy_slots(
                slot_start, slot_end, busy_slots
            ):
                slot_jsondict = {
                    "id": f"{uuid1()}",
                    "resourceType": "Slot",
                    "schedule": {"reference": f"Schedule/{schedule_id}"},
                    "status": "free",
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                }
                slot = construct_fhir_element(
                    slot_jsondict["resourceType"], slot_jsondict
                )
                slots.append(slot)

            slot_start += duration

        return None, slots

    def _does_slot_time_inside_availability(
        self,
        slot_start: datetime,
        slot_end: datetime,
        timezone: pytz.timezone,
        available_time: list[PractitionerRoleAvailableTime],
    ):
        slot_start = slot_start.astimezone(tz=timezone)
        slot_end = slot_end.astimezone(tz=timezone)
        date_of_week = slot_start.strftime("%a").lower()
        for role_time in available_time:
            if date_of_week not in role_time.daysOfWeek:
                continue
            if role_time.availableStartTime <= slot_start.time() and (
                # For cases where practitioner works until midnight
                role_time.availableEndTime == time(0, 0)
                or (
                    slot_end.time() != time(0, 0)
                    and slot_end.time() <= role_time.availableEndTime
                )
            ):
                return True
        return False

    def _does_slot_time_overlap_with_busy_slots(
        self, slot_start: datetime, slot_end: datetime, busy_slots: list[Slot]
    ):
        for busy_slot in busy_slots:
            # If overlap happened then return true. For overlap logic, see
            # https://stackoverflow.com/questions/325933/determine-whether-two-date-ranges-overlap
            if slot_start < busy_slot.end and slot_end > busy_slot.start:
                return True
        return False

    def _ceil_time(self, time: datetime, delta: timedelta):
        return time + (datetime.min.replace(tzinfo=pytz.UTC) - time) % delta

    def _search_slots(self, search_clause) -> list[DomainResource]:
        slots = []

        result = self.resource_client.search("Slot", search_clause)
        if result.entry is not None:
            for entry in result.entry:
                slots.append(entry.resource)

        return slots
