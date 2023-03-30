from enum import Enum
from typing import Tuple, Union
from uuid import UUID, uuid4

from fhir.resources import construct_fhir_element
from fhir.resources.questionnaireresponse import QuestionnaireResponse

from adapters.fhir_store import ResourceClient


class QuestionnaireResponseStatus(Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    STOPPED = "stopped"


class QuestionnaireResponseService:
    """Service class for managing questionnaire response."""

    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def insert_questionnaire_response(
        self, request_data: dict, patient_id: UUID, questionnaire_id: UUID
    ) -> Tuple:
        questionnaire_response = {
            "resourceType": "QuestionnaireResponse",
            "id": str(uuid4()),
            "subject": {"reference": f"Patient/{patient_id}"},
            "questionnaire": f"{questionnaire_id}",
        }

        questionnaire_response_item = request_data.get("item")
        questionnaire_response["item"] = questionnaire_response_item

        questionnaire_response["status"] = self.get_questionnaire_status(
            questionnaire_id, questionnaire_response_item
        )

        fhir_prequestionnaire_response = construct_fhir_element(
            "QuestionnaireResponse", questionnaire_response
        )

        fhir_prequestionnaire_response = self.resource_client.create_resource(
            fhir_prequestionnaire_response
        )

        return None, fhir_prequestionnaire_response

    def update_questionnaire_response(self, response_id: UUID, request_data: dict):
        questionnaire_response = self.resource_client.get_resource(
            response_id, "QuestionnaireResponse"
        ).dict()

        questionnaire_response_item = request_data.get("item")

        updated_questionnaire_response = QuestionnaireResponse(
            id=str(response_id),
            status=self.get_questionnaire_status(
                questionnaire_response["questionnaire"], questionnaire_response_item
            ),
            questionnaire=questionnaire_response["questionnaire"],
            subject=questionnaire_response["subject"],
            item=questionnaire_response_item,
        )

        updated_questionnaire_response = self.resource_client.put_resource(
            response_id, updated_questionnaire_response
        )

        return updated_questionnaire_response

    def __len__(self, questionnaire_id: UUID) -> int:
        questionnaire = self.resource_client.get_resource(
            questionnaire_id, "Questionnaire"
        ).dict()

        if "item" not in questionnaire:
            return 0

        return len(questionnaire["item"])

    def find_response_id(self, patient_id, questionnaire_id) -> Union[str, None]:
        questionnare_responses = self.resource_client.get_resources(
            "QuestionnaireResponse"
        )

        if questionnare_responses is None:
            return None

        for response in questionnare_responses.entry:
            resource = response.resource.dict()
            if (
                resource["questionnaire"] == questionnaire_id
                and resource["subject"]["reference"].split("/")[1] == patient_id
            ):
                return resource["id"]

        return None

    def get_questionnaire_status(
        self, questionnaire_id, questionnaire_response_item
    ) -> str:
        status = (
            QuestionnaireResponseStatus.COMPLETED.value
            if len(questionnaire_response_item) == self.__len__(questionnaire_id)
            else QuestionnaireResponseStatus.IN_PROGRESS.value
        )

        return status
