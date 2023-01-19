# kitsune-backend

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Build Status](https://dev.azure.com/UMedInc/Kitsune/_apis/build/status/kitsune-backend?branchName=akirakakar%2F150%2Fcloudrun)](https://dev.azure.com/UMedInc/Kitsune/_build/latest?definitionId=6&branchName=akirakakar%2F150%2Fcloudrun)

## Prerequisite

- [python](https://www.python.org/downloads/)
- [poetry](https://python-poetry.org/docs/#installation)
- [pre-commit](https://pre-commit.com/)

## Development

### Dependencies management

This project uses `poetry` to manage dependencies. The `pyproject.toml` file
is for dependencies declaration, and the `poetry.lock` file is for locking
dependencies for the current version.

More information can be found on the [official
documentation](https://python-poetry.org/docs/).

### Run the application

There are two ways to run the application: either inside a container or outside
a container. It's recommended to run the application inside a container, so that
it closely matches how the deployment works in production.

All the tutorials below are based on running the application inside a container.
But in case you want to skip the container part, simply run:

```shell
poetry install && poetry run python src/app.py
```

#### Running development environment

`sample001:1.0` can be replaced with any tag you want

```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -p 8003:8080 sample001:1.0
```

For most API to work, you need your own `service.json` file, obtained from
gcloud. See [here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys).
Then you also need to grant your service account access to various resource (for
example, the FHIR store).
You can use env for secrets path but production system picks it up automatically in cloudrun.
When you are mounting secret files, you need to create a file in local env and mount the destination.
Currently in the example below uses /secrets/stripe_key but it can be anywhere with a read permissions.
Destination of where you are mounting to needs to have a write permission.

To run your image and set the `service.json`

```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -v /secrets/stripe_key:/home/secrets -p 8003:8080 -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/service.json -e SECRETS_PATH=/home/secrets sample001:1.0
```

This repository also provides a convienent `local.env.example` file for common environment
variables required to run the service locally. To use the `local.env` file:

```shell
cp local.env.example local.env
```

And then run the following to stub the env file to the docker

```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -v /secrets/stripe_key:/secrets/stripe_key -p 8003:8080 --env-file local.env sample001:1.0
```

#### If you are using VSCode

- Click on the "Open Remote Window" button on the bottom left
- Click on "Reopen in container"
- This will open the project in a docker container
- Once that loads
- run this command

```bash
#!/bin/bash
mkdir /secrets && echo <Your Stripe Key> > /secrets/stripe_key

mkdir -p /secrets/orca_apikey /secrets/orca_cert_pass /secrets/orca_client_cert /secrets/orca_fqdn /secrets/notion_key /secrets/twilio_account_sid /secrets/twilio_verify_service_sid /secrets/twilio_auth_token

echo <Your notion Key>  > /notion_key/notion_key
echo  <Your account id> > /secrets/twilio_account_sid/twilio_account_sid
echo  <Your account id> > /secrets/twilio_auth_token/twilio_auth_token
echo  <Your account id> > /secrets/twilio_verify_service_sid/twilio_verify_service_sid
echo "api key" > /secrets/orca_apikey/orca_apikey
echo "pass" > /secrets/orca_cert_pass/orca_cert_pass

openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/CN=umed.jp"
openssl pkcs12 -export -out orca_client_cert -in cert.pem -inkey key.pem -passout pass:pass
cp orca_client_cert /secrets/orca_client_cert/orca_client_cert
echo "demo-weborca.cloud.orcamo.jp" > /secrets/orca_fqdn/orca_fqdn
```

- this should create a secrets/stripe_key folder in the root directory
- Then go back to the workspace kitsune-backend
- Then run

poetry install
export the environment variables into the terminal
poetry run python srs/app.py
```

You should have your endpoint running at `http://localhost:8080`

#### Running unit tests and coverage

```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -it sample001:1.0 pytest
```

#### Running unit tests and coverage in docker

```shell
poetry run pytest
```

#### Running production environment

```shell
docker build --target production -t sample001:1.0 -f docker/Dockerfile .
docker run -p 8003:8080 --env-file local.env sample001:1.0
```

### Curl the endpoint with Firebase credential

First you need to retrieve the `idToken` from itentity toolkit:

```shell
curl 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyD74Q7vKczSzW9NQCXP7wnZ3cCmCkk3yRk' \
-H 'Content-Type: application/json' \
--data-binary '{"email":[REDACTED],"password":[REDACTED],"returnSecureToken":true}'
```

Then, pass the `idToken` in the authorization header. For example:

```shell
curl -H "Authorization: Bearer [idToken]" http://localhost:8003/patients/bf8eb518-64c4-4f4a-b5e7-64a9435539e6
```

### Run on cloud run

If you merge your change, CICD pipeline will automatically deploy to cloud run.

## Test

To run the integration tests: `poetry run pytest -s -vv integtest/`

Setup env vars:

1. copy the env var template: `cp local.env.example local.env`
2. setup the env vars
3. export those env vars to local env: `set -a && . ./local.env && set +a`
4. run test: `poetry run pytest`

## Before Commit and Push code

There are number of tests you can conduct before raising PR to save everyone's time. (CI can fail) Here are a few that we thought about. If you can come up something else that can improve code quality and stability, please update this section.

### Unittest and Code Coverage

- Code Coverage has not decreased since you added new code
- All unittests have passed

### Make sure pre-commit is installed before commit

- If it's not installed or edited `.pre-commit-config.yaml`, you can run `pre-commit install`
- If you have already commited code, you can also run `pre-commit run --all-files`
