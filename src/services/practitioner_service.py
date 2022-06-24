from typing import List

from fhir.resources import construct_fhir_element
from fhir.resources.domainresource import DomainResource

from adapters.fhir_store import ResourceClient
from utils.system_code import SystemCode

SUPPORTED_LANGUAGE = {"en", "ja"}


class HumanName:
    def __init__(
        self,
        given_name: str,
        family_name: str,
        language: str,
        role_type: str = "doctor",
    ):
        self.given_name = given_name
        self.family_name = family_name
        self.language = language
        self.role_type = role_type

        if language not in SUPPORTED_LANGUAGE:
            raise NotImplementedError()

    def get_name_with_lang(self):
        language_map = {"ja": "IDE", "en": "ABC"}
        language_url = (
            "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation"
        )
        output = {
            "family": self.family_name,
            "given": [self.given_name],
            "text": f"{self.given_name} {self.family_name}",
            "extension": [
                {"url": language_url, "valueString": language_map[self.language]},
            ],
        }

        if self.language == "en":
            if self.role_type == "doctor":
                output["prefix"] = ["MD"]
            elif self.role_type == "nurse":
                output["prefix"] = ["Nurse"]
            elif self.role_type == "staff":
                output["prefix"] = ["Administrative healthcare staff"]
        elif self.language == "ja":
            if self.role_type == "doctor":
                output["prefix"] = ["医師"]
            elif self.role_type == "nurse":
                output["prefix"] = ["看護師"]
            elif self.role_type == "staff":
                output["prefix"] = ["医療事務"]

        return output


class Biography:
    def __init__(self, content: str, language: str):
        self.content = content
        self.language = language

        if language not in SUPPORTED_LANGUAGE:
            raise NotImplementedError()

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
        if photo and not photo.startswith(base64_prefix):
            return Exception("Wrong photo format"), None

        bio_extensions = [bio.get_bio_with_lang() for bio in biographies]
        modified_names = [name.get_name_with_lang() for name in names]
        practitioner_jsondict = {
            "resourceType": "Practitioner",
            "active": True,
            "name": modified_names,
            "telecom": [{"system": "email", "value": email, "use": "work"}],
            "gender": gender,
            "communication": [{"coding": [communication]}],
            "extension": bio_extensions,
            "photo": [],
        }

        if photo:
            practitioner_jsondict["photo"].append(
                {"contentType": "image/png", "data": photo[len(base64_prefix) :]}
            )

        practitioner = construct_fhir_element("Practitioner", practitioner_jsondict)
        practitioner = self.resource_client.get_post_bundle(practitioner, identity)
        return None, practitioner

    def update_practitioner(
        self,
        practitioner: DomainResource,
        biographies: List[Biography],
        names: List[HumanName],
        photo: str = None,
        gender: str = None,
    ):
        base64_prefix = "data:image/png;base64,"
        if photo and not photo.startswith(base64_prefix):
            return Exception("Wrong photo format"), None
        bio_extensions = [bio.get_bio_with_lang() for bio in biographies]
        modified_names = [name.get_name_with_lang() for name in names]
        modified = False
        if modified_names:
            practitioner.name = modified_names
            modified = True
        if bio_extensions:
            practitioner.extension = bio_extensions
            modified = True
        if photo:
            practitioner.photo = [
                {"contentType": "image/png", "data": photo[len(base64_prefix) :]}
            ]
            modified = True
        if gender:
            practitioner.gender = gender
            modified = True
        if modified:
            practitioner_bundle = self.resource_client.get_put_bundle(
                practitioner, practitioner.id
            )
            return None, practitioner_bundle
        return None, None
