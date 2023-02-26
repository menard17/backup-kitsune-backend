import argparse
import csv
from os.path import exists
import structlog
import firebase_admin

from adapters.fhir_store import ResourceClient
from services.patient_service import PatientService

log = structlog.get_logger()


def bind_ids(filepath: str):
    _ = firebase_admin.initialize_app()

    resource_client = ResourceClient()
    patient_service = PatientService(resource_client)

    log.info(f"Start bind orca ID to patient ID with the file: {filepath}")
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            patient_id, orca_id = row["patient_id"], row["orca_id"]
            log.info(f"binding patient: [{patient_id}] with orca_id: [{orca_id}].")
            err, _ = patient_service.update(patient_id, orca_id=orca_id)
            if err is not None:
                raise Exception(str(err))
    log.info("Orca ID binding finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bind Orca ID to Patient")
    parser.add_argument("--filepath", help="The file path with the patient ID => OrcaID binding", type=str)
    args = parser.parse_args()

    if not exists(args.filepath):
        raise Exception("non-existing file")
    if not args.filepath.endswith(".csv"):
        raise Exception("unexpected type of file")

    bind_ids(args.filepath)
