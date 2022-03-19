from typing import Dict, Tuple

from pytest_bdd import given, scenarios, then

from adapters.fhir_store import ResourceClient
from integtest.characters import Practitioner
from integtest.conftest import Client
from integtest.utils import create_practitioner, create_user
from services.practitioner_role_service import PractitionerRoleService

scenarios("../features/get_practitioner_name.feature")


@given("doctor A", target_fixture="doctor_a")
def get_doctor_a(client: Client) -> Practitioner:
    name = ("doctorA last name", "doctorA first name")
    user = create_user()
    return create_practitioner(client, user, practitioner_name=name)


@given("doctor B", target_fixture="doctor_b")
def get_doctor_b(client: Client) -> Practitioner:
    name = ("doctorB last name", "doctorB first name")
    user = create_user()
    return create_practitioner(client, user, practitioner_name=name)


@given("doctor C", target_fixture="doctor_c")
def get_doctor_c(client: Client) -> Practitioner:
    name = ("doctorC last name", "doctorC first name")
    user = create_user()
    return create_practitioner(client, user, practitioner_name=name)


@then("name of doctors can be fetched")
def get_doctor_names(
    doctor_a: Practitioner, doctor_b: Practitioner, doctor_c: Practitioner
):
    practitioner_role_service = PractitionerRoleService(
        resource_client=ResourceClient()
    )
    _, actual_doctor_a = practitioner_role_service.get_practitioner_name(
        "ABC", doctor_a.fhir_data["id"]
    )
    _, actual_doctor_b = practitioner_role_service.get_practitioner_name(
        "ABC", doctor_b.fhir_data["id"]
    )
    _, actual_doctor_c = practitioner_role_service.get_practitioner_name(
        "ABC", doctor_c.fhir_data["id"]
    )

    assert actual_doctor_a == _convert_name_to_dict(doctor_a.practitioner_name)
    assert actual_doctor_b == _convert_name_to_dict(doctor_b.practitioner_name)
    assert actual_doctor_c == _convert_name_to_dict(doctor_c.practitioner_name)


def _convert_name_to_dict(name: Tuple) -> Dict:
    return {
        "family": name[0],
        "given": [name[1]],
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/iso21090-EN-representation",
                "valueString": "ABC",
            }
        ],
        "prefix": ["MD"],
        "text": f"{name[1]} {name[0]}",
    }
