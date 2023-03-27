"""
https://build.fhir.org/questionnaire.html
"""
from enum import Enum
from typing import Any, Dict, List, Tuple, Union
from uuid import uuid4

from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient


# + Rule: If there are more than one enableWhen, enableBehavior must be specified
class EnableBehavior(Enum):
    ALL = "all"
    ANY = "any"
    NONE = "none"


ENABLE_BEHAVIOR_NUMBER = 1


class PrequestionnaireService:
    """Service class for managing prequestionnaire."""

    GENDER_QUESTION_TEXT = "What is your gender?"

    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def add_question(
        self, request_data: dict, questionnaire_data: dict
    ) -> Tuple[Exception, DomainResource]:
        """Adds a question to the prequestionnaire.

        Args:
            request_data: A dictionary containing the new question data.
            questionnaire_data: A dictionary containing the existing prequestionnaire data.

        Returns:
            If successful, returns the updated questionnaire data.
            If unsuccessful, returns None.
        """
        question_item = {
            "linkId": str(uuid4()),
            "text": request_data["text"],
            "type": request_data["type"],
        }

        enable_conditions = []
        localization_list = self.get_localization_items(
            request_data.get("localization", [])
        )

        question_item["extension"] = localization_list
        enable_conditions = self.get_enable_conditions(request_data, questionnaire_data)
        if "answerOption" in request_data and request_data["type"] == "choice":
            question_item["answerOption"] = request_data["answerOption"]

        if enable_conditions:
            question_item["enableWhen"] = enable_conditions

        if len(enable_conditions) > ENABLE_BEHAVIOR_NUMBER:
            question_item["enableBehavior"] = EnableBehavior.ALL.value

        # Add item to prequestionnaire resource
        questionnaire_data.item = questionnaire_data.item or []
        questionnaire_data.item.append(question_item)

        # Update prequestionnaire resource in FHIR server
        updated_questionnaire_data = self.resource_client.put_resource(
            questionnaire_data.id, questionnaire_data
        )

        return None, updated_questionnaire_data

    def add_gender_question(self, questionnaire_data: dict) -> str:
        id = str(uuid4())
        question_item = {
            "linkId": id,
            "text": self.GENDER_QUESTION_TEXT,
            "type": "text",
        }

        questionnaire_data.item = questionnaire_data.item or []
        questionnaire_data.item.append(question_item)

        self.resource_client.put_resource(questionnaire_data.id, questionnaire_data)

        return id

    def get_gender_question_id(self, questionnaire_data: dict) -> str:
        if "item" not in questionnaire_data:
            return None

        for question in questionnaire_data["item"]:
            if "text" in question and question["text"] == self.GENDER_QUESTION_TEXT:
                return question["linkId"]

        return None

    def validate_questionnaire_item(self, request_data: dict) -> Union[dict, None]:
        """
        Validate request data for creating a questionnaire item.
        """
        required_fields = ["text", "type"]

        if not all(field in request_data for field in required_fields):
            missing_fields = [
                field for field in required_fields if field not in request_data
            ]
            error_msg = f"Missing required field(s): {', '.join(missing_fields)}"
            return {"error": error_msg}

        item_type = request_data["type"]
        if item_type == "choice" and "answerOption" not in request_data:
            return {"error": "Missing required field: answerOption"}

        return None

    def get_localization_items(
        self, localization_data: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        localization_items = []
        for item in localization_data:
            localization_item = {
                "url": "http://hl7.org/fhir/StructureDefinition/questionnaire-display",
                "valueString": item["text"],
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/questionnaire-display",
                        "valueCode": item["code"],
                    }
                ],
            }
            localization_items.append(localization_item)
        return localization_items

    def get_enable_conditions(
        self, request_data: dict, fhir_prequestionnaire: dict
    ) -> dict:
        enable_conditions = []
        if "enableWhen" in request_data:
            enable_conditions.extend(request_data["enableWhen"])
        if "gender_condition" in request_data:
            gender_question_exist_id = self.get_gender_question_id(
                fhir_prequestionnaire.dict()
            )
            gender_question_link_id = (
                gender_question_exist_id
                if gender_question_exist_id
                else self.add_gender_question(fhir_prequestionnaire)
            )
            enable_conditions.append(
                {
                    "answerCoding": {
                        "system": "http://hl7.org/fhir/administrative-gender",
                        "display": request_data["gender_condition"],
                    },
                    "operator": "=",
                    "question": gender_question_link_id,
                }
            )
        return enable_conditions

    def rearrange_question(
        self, fhir_questionnaire: dict, index_to_move: int, link_id: str
    ) -> Tuple:
        """
        Rearrange the questionnaire item based on the current index, index to move and linkId.

        Args:
            fhir_questionnaire: A dict Questionnaire resource object.
            index_to_move: The index to move the questionnaire item to.
            link_id: The linkId of the questionnaire item to move.

        Returns:
            If successful, returns the updated questionnaire data.
            If unsuccessful, returns None.
        """
        # Get the item to move and remove it from the questionnaire
        item_to_move = None
        for item in fhir_questionnaire.item:
            if item.linkId == link_id:
                item_to_move = item
                fhir_questionnaire.item.remove(item)
                break

        # Insert the item to move at the new index
        fhir_questionnaire.item.insert(index_to_move, item_to_move)

        # Update the questionnaire resource in FHIR server
        updated_questionnaire = self.resource_client.put_resource(
            fhir_questionnaire.id, fhir_questionnaire
        )

        return None, updated_questionnaire
