import json

from adapters.fhir_store import ResourceClient


class ListsService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def dequeue(self, list_id: str):
        "for get top patient in the list"
        fhir_list = self.resource_client.get_resource(list_id, "List")
        if fhir_list.entry is None:
            return None, None
        queue = json.loads(fhir_list.json())
        first_patient = queue["entry"][0]["item"]["reference"].split("/")[1]
        for idx, e in enumerate(fhir_list.entry):
            if e.item.reference.split("/")[1] == first_patient:
                patient_list_idx = idx
        # remove the item of the patient from the entry
        entry = fhir_list.entry
        fhir_list.entry = entry[:patient_list_idx] + entry[patient_list_idx + 1 :]
        lists = self.resource_client.get_put_bundle(fhir_list, fhir_list.id)

        return first_patient, lists
