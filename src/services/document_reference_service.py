from datetime import datetime, timezone

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode


class DocumentReferenceService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_document_reference(
        self, subject, document_type, pages, practitioner_role_id, encounter_id
    ):
        contents = []
        for page in pages:
            content = {}
            if page.get("url"):
                content["attachment"] = {"url": page["url"]}
            if page.get("data"):
                content["attachment"] = {
                    "data": page["data"],
                    "contentType": "text/xml;charset=utf-8",
                }
            content["attachment"]["creation"] = datetime.now(timezone.utc)
            content["attachment"]["title"] = page["title"]
            contents.append(content)

        document_reference_jsondict = {
            "resourceType": "DocumentReference",
            "status": "current",
            "subject": {
                "reference": subject,
            },
            "date": datetime.now(timezone.utc),
            "type": {"coding": [SystemCode.document_type_code(document_type)]},
            "content": contents,
        }

        if practitioner_role_id:
            document_reference_jsondict["author"] = [
                {"reference": f"PractitionerRole/{practitioner_role_id}"}
            ]

        if encounter_id:
            document_reference_jsondict["context"] = {
                "encounter": [{"reference": f"Encounter/{encounter_id}"}],
            }

        if category := SystemCode.document_category_code(document_type):
            document_reference_jsondict["category"] = [{"coding": [category]}]

        document_reference = construct_fhir_element(
            document_reference_jsondict["resourceType"], document_reference_jsondict
        )

        # get previously existing items to ensure only the newly added item will be active
        search_clause = []
        search_clause.append(("subject", subject))
        search_clause.append(("type", SystemCode.document_type_token(document_type)))
        search_clause.append(("status", "current"))
        existing = self.resource_client.search(
            "DocumentReference",
            search=search_clause,
        )

        # change status of previously existing items to "superseded"
        if existing.entry:
            for e in existing.entry:
                self.resource_client.patch_resource(
                    e.resource.id,
                    "DocumentReference",
                    [{"op": "add", "path": "/status", "value": "superseded"}],
                )

        document_reference = self.resource_client.create_resource(document_reference)

        return document_reference

    def search_document_reference(
        self, subject, date, document_type, page_count, status
    ):

        search_clause = []

        search_clause.append(("subject", subject))

        if date:
            search_clause.append(("date", date))

        if document_type:
            search_clause.append(
                ("type", SystemCode.document_type_token(document_type))
            )

        if page_count:
            search_clause.append(("_count", page_count))
        else:
            search_clause.append(("_count", "10"))

        if not status:
            search_clause.append(("status", "current"))
        else:
            search_clause.append(("status", status))

        search_clause.append(("_sort", "-lastUpdated"))

        result = self.resource_client.search(
            "DocumentReference",
            search=search_clause,
        )

        return result
