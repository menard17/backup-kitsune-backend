## Scripts

### generate_metric_dashboard_data.py

A script that output json files that can be used in the `kitsune-backend-metrics`.

To run the script: `poetry run python src/scripts/generate_metric_dashboard_data.py`

It will generate a `data/` folder with the metric and dashboard terraform setup json data. Please copy the whole `data/` folder to the `infra` repo: `infra/terraform/modules/kitsune-backend-metrics/` and commit the data folder there.
