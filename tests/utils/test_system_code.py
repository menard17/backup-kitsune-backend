from utils.system_code import SystemCode


def test_walkin_appointment_service():
    # Given
    service_type = "walkin"
    expected = {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
        "code": "WALKIN",
        "display": "A previously unscheduled walk-in visit",
    }

    # When
    actual = SystemCode.appointment_service_type(service_type)

    # Then
    assert expected == actual


def test_routine_appointment_service():
    # Given
    service_type = "routine"
    expected = {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
        "code": "ROUTINE",
        "display": "Routine appointment",
    }

    # When
    actual = SystemCode.appointment_service_type(service_type)

    # Then
    assert expected == actual


def test_other_appointment_service():
    # Given
    service_types = ["random", "WALKIN", ""]
    expected = {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
        "code": "FOLLOWUP",
        "display": "A follow up visit from a previous appointment",
    }

    # When and Then
    for service_type in service_types:
        assert expected == SystemCode.appointment_service_type(service_type)


def test_cancel_type_from_portal():
    # Given
    appointment_cancel_type = "portal"
    expectecd = {
        "system": "http://terminology.hl7.org/CodeSystem/appointment-cancellation-reason",
        "code": "pat-cpp",
        "display": "Patient: Canceled via Patient Portal",
    }

    # When
    actual = SystemCode.appointment_cancel_type(appointment_cancel_type)

    # Then
    assert expectecd == actual


def test_cancel_type_patient():
    # Given
    appointment_cancel_type = "patient"
    expectecd = {
        "system": "http://terminology.hl7.org/CodeSystem/appointment-cancellation-reason",
        "code": "pat",
        "display": "Patient",
    }

    # When
    actual = SystemCode.appointment_cancel_type(appointment_cancel_type)

    # Then
    assert expectecd == actual
