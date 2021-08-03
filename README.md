# kitsune-backend

## Prerequisite
* [python](https://www.python.org/downloads/)
* [poetry](https://python-poetry.org/docs/#installation)

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
poetry install
poetry run python src/app.py
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

To run your image and set the `service.json`
```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -p 8003:8080 -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/service.json sample001:1.0
```

This repository also provides a convienent `dev.env` file for common environment
variables required to run the service locally. To use the `local.env` file:
```
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -p 8003:8080 --env-file local.env sample001:1.0
```

#### Running unit tests and coverage

```shell
docker build --target development -t sample001:1.0 -f docker/Dockerfile .
docker run -it sample001:1.0 coverage run --rcfile ./pyproject.toml -m pytest ./tests
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

To run the integration tests: `poetry run pytest -s -vv src/integtest/`

Setup env vars:
1. `FIREBASE_API_KEY`
2. `ORIGINS` (can be set as `"*"`)
