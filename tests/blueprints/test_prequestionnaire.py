import json

from fhir.resources import construct_fhir_element
from helper import FakeRequest, MockResourceClient

from blueprints.prequestionnaire import PrequestionnaireController

PREQUESTIONNAIRE_DATA = {
    "resourceType": "Questionnaire",
    "id": "test-id-29742652",
    "status": "active",
    "subjectType": ["Patient"],
}

PREQUESTIONNAIRE_DATA_WITH_ITEM = {
    "resourceType": "Questionnaire",
    "id": "test-id-29742652",
    "status": "active",
    "subjectType": ["Patient"],
    "item": [
        {
            "linkId": "test-id-545351",
            "text": "Example question text",
            "type": "string",
        }
    ],
}

ITEM_DATA_STRING = {
    "linkId": "test-id-545351",
    "text": "Example question text",
    "type": "string",
}

ITEM_DATA_STRING_NO_TEXT = {
    "linkId": "test-id-545351",
    "type": "string",
}

ITEM_DATA_STRING_NO_TYPE = {
    "linkId": "test-id-545351",
    "text": "Example question text",
}

ITEM_DATA_STRING_NO_TYPE_AND_TEXT = {
    "linkId": "test-id-545351",
}


ITEM_DATA_CHOICE_NO_OPTIONS = {
    "linkId": "test-id-5654t5",
    "text": "Example question choice",
    "type": "choice",
}

ITEM_DATA_CHOICE = {
    "linkId": "test-id-5654t5",
    "text": "Example question choice",
    "type": "choice",
    "answerOption": [
        {"valueCoding": {"display": "Yes"}},
        {"valueCoding": {"display": "No"}},
    ],
}

ITEM_DATA_STRING_UPDATED = {
    "linkId": "test-id-545351",
    "text": "update text",
    "type": "string",
}


def test_create_questionnaire():
    def mock_create_resource(fhir_questionnaire):
        assert fhir_questionnaire.status == "active"
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA)

    resource_client = MockResourceClient()
    resource_client.create_resource = mock_create_resource

    controller = PrequestionnaireController(resource_client)
    resp = controller.create()
    assert resp.status_code == 201
    assert json.loads(resp.data)["id"] == PREQUESTIONNAIRE_DATA["id"]


def test_create_item_in_questionnaire_invalid_text():
    resource_client = MockResourceClient()

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_STRING_NO_TEXT),
    )

    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 400
    assert "Missing required field(s): text" in resp.data.decode("utf-8")


def test_create_item_in_questionnaire_invalid_type():
    resource_client = MockResourceClient()

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_STRING_NO_TYPE),
    )

    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 400
    assert "Missing required field(s): type" in resp.data.decode("utf-8")


def test_create_item_in_questionnaire_invalid_type_and_text():
    resource_client = MockResourceClient()

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_STRING_NO_TYPE_AND_TEXT),
    )
    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 400
    assert "Missing required field(s): text, type" in resp.data.decode("utf-8")


def test_create_item_in_questionnaire_type_choice_no_option():
    resource_client = MockResourceClient()

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_CHOICE_NO_OPTIONS),
    )

    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 400
    assert "Missing required field: answerOption" in resp.data.decode("utf-8")


def test_create_item_in_questionnaire_type_string_success():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA["id"]
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA)

    def mock_put_resource(questionnaire_id, quetionnaire_data):
        assert questionnaire_id == PREQUESTIONNAIRE_DATA["id"]
        return construct_fhir_element("Questionnaire", quetionnaire_data)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_STRING),
    )

    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 201
    assert json.loads(resp.data)["id"] == PREQUESTIONNAIRE_DATA["id"]


def test_create_item_in_questionnaire_type_choice_success():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA["id"]
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA)

    def mock_put_resource(questionnaire_id, quetionnaire_data):
        assert quetionnaire_data.item[0]["text"] == ITEM_DATA_CHOICE["text"]
        assert questionnaire_id == PREQUESTIONNAIRE_DATA["id"]
        return construct_fhir_element("Questionnaire", quetionnaire_data)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_CHOICE),
    )

    controller = PrequestionnaireController(resource_client)
    resp = controller.create_questionnaire_item(PREQUESTIONNAIRE_DATA["id"], request)
    assert resp.status_code == 201
    assert json.loads(resp.data)["id"] == PREQUESTIONNAIRE_DATA["id"]


def test_update_question():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA_WITH_ITEM)

    def mock_put_resource(questionnaire_id, quetionnaire_data):
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", quetionnaire_data)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    request = FakeRequest(
        data=json.dumps(ITEM_DATA_STRING_UPDATED),
    )
    controller = PrequestionnaireController(resource_client)
    resp = controller.update_question(
        ITEM_DATA_STRING["linkId"], PREQUESTIONNAIRE_DATA_WITH_ITEM["id"], request
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["id"] == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
    assert json.loads(resp.data)["item"][0]["text"] == "update text"


def test_remove_question():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA_WITH_ITEM)

    def mock_put_resource(questionnaire_id, quetionnaire_data):
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", quetionnaire_data)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    controller = PrequestionnaireController(resource_client)
    resp = controller.remove_question(
        ITEM_DATA_STRING["linkId"], PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
    )

    assert resp.status_code == 200
    assert json.loads(resp.data)["id"] == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
    assert "items" not in json.loads(resp.data)


def test_remove_question_does_not_exists():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return []

    def mock_put_resource(questionnaire_id, quetionnaire_data):
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", quetionnaire_data)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource
    resource_client.put_resource = mock_put_resource

    controller = PrequestionnaireController(resource_client)
    resp = controller.remove_question(
        ITEM_DATA_STRING["linkId"], PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
    )

    assert resp.status_code == 404
    assert resp.data.decode("utf-8") == "No questionnaire found"


def test_get_questionnaire():
    def mock_get_resource(questionnaire_id, resource_type):
        assert resource_type == "Questionnaire"
        assert questionnaire_id == PREQUESTIONNAIRE_DATA_WITH_ITEM["id"]
        return construct_fhir_element("Questionnaire", PREQUESTIONNAIRE_DATA_WITH_ITEM)

    resource_client = MockResourceClient()
    resource_client.get_resource = mock_get_resource

    controller = PrequestionnaireController(resource_client)
    resp = controller.get_prequestionnaire(PREQUESTIONNAIRE_DATA_WITH_ITEM["id"])

    assert json.loads(resp.data) == PREQUESTIONNAIRE_DATA_WITH_ITEM
