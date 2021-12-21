from typing import List

from fhir.resources import construct_fhir_element

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode


class HumanName:
    def __init__(self, given_name: str, family_name: str, langauge: str):
        self.given_name = given_name
        self.family_name = family_name
        self.language = langauge

    def get_name_with_lang(self):
        language_map = {"ja": "IDE", "en": "ABC"}
        language_url = (
            "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation"
        )
        output = {
            "family": self.family_name,
            "given": [self.given_name],
            "extension": [
                {"url": language_url, "valueString": language_map[self.language]},
            ],
        }

        if self.language == "en":
            output["prefix"] = ["Dr."]
        if self.language == "ja":
            output["suffix"] = ["先生"]

        return output


class Biography:
    def __init__(self, content: str, language: str):
        self.content = content
        self.language = language

    def get_bio_with_lang(self):
        language_ext = "http://hl7.org/fhir/StructureDefinition/translation"
        output = {
            "url": "bio",
            "valueString": self.content,
            "extension": [{"url": language_ext, "valueString": self.language}],
        }
        return output


class PractitionerService:
    def __init__(self, resource_client: ResourceClient) -> None:
        self.resource_client = resource_client

    def create_practitioner(
        self,
        identity: str,
        email: str,
        photo: str,
        gender: str,
        biographies: List[Biography],
        names: List[HumanName],
    ):
        communication = SystemCode.communication("ja")
        base64_prefix = "data:image/png;base64,"
        if not photo.startswith(base64_prefix):
            return Exception("Wrong photo format"), None

        bio_extensions = [bio.get_bio_with_lang() for bio in biographies]
        names = [name.get_name_with_lang() for name in names]
        practitioner_jsondict = {
            "resourceType": "Practitioner",
            "active": True,
            "name": names,
            "telecom": [{"system": "email", "value": email, "use": "work"}],
            "gender": gender,
            "communication": [{"coding": [communication]}],
            "extension": bio_extensions,
            "photo": [
                {"contentType": "image/png", "data": photo[len(base64_prefix) :]}
            ],
        }

        practitioner = construct_fhir_element("Practitioner", practitioner_jsondict)
        practitioner = self.resource_client.get_post_bundle(practitioner, identity)
        return None, practitioner
