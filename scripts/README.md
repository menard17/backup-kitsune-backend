# Operation Scripts

## bind_orca_id.py

This scripts binds the orca IDs to patient IDs. The mapping of the patient ID and the Orca ID must be in a CSV file with the following format:

```csv
patient_id,orca_id
<:patient-id-1>, <:orca-id-1>
<:patient-id-2>, <:orca-id-2>
.
.
.
```
The CSV file should be under the `scripts/orca_bindings/` folder.

This script can be run with the following command:
```
poetry run python scripts/bind_orca_id.py --filepath=<:csv-file-path>
```
For instance:

```
poetry run python scripts/bind_orca_id.py --filepath="./scripts/orca_bindings/dev/2023-01-21.csv"
```
