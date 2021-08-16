from utils.middleware import is_authorized


def test_patient_should_access_to_their_resources():
    assert is_authorized("Patient", "patient_id", "Patient", "patient_id") is True


def test_patient_should_not_have_access_to_other_patients():
    assert is_authorized("Patient", "patient_id", "Patient", "other_id") is False
    assert is_authorized("Patient", "patient_id", "Patient", "*") is False


def test_doctor_should_have_access_to_all_patients():
    assert is_authorized("Doctor", "doctor_id", "Patient", "patient_id") is True
    assert is_authorized("Doctor", "doctor_id", "Patient", "*") is True
