# kitsune-backend

## Run locally inside of docker image
Within the devcontainer, you can just run
```bash
>>> python app.py
```

## Run locally from outside of docker image
sample001 can be replaced with any tag you want

```bash
>>> docker build  -t sample001:1.0 .
>>> docker run -p 8003:8080 sample001:1.0
```

For most API to work, you need your own `service.json` file, obtained from gcloud. See [here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys). Then you also need to grant your service account access to various resource (for example, the FHIR store).

To run your image and set the `service.json`
```bash
>>> docker build  -t sample001:1.0 .
>>> docker run -p 8003:8080 -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/service.json sample001:1.0
```

## Curl the endpoint with Firebase credential

First you need to retrieve the `idToken` from itentity toolkit:

```bash
curl 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyD74Q7vKczSzW9NQCXP7wnZ3cCmCkk3yRk' \
-H 'Content-Type: application/json' \
--data-binary '{"email":[REDACTED],"password":[REDACTED],"returnSecureToken":true}'
```

Then, pass the `idToken` in the authorization header. For example:
```bash
curl -H "Authorization: Bearer [idToken]" http://localhost:8003/patients/bf8eb518-64c4-4f4a-b5e7-64a9435539e6
```


## Run on cloud run
If you merge your change, CICD pipeline will automatically deploy to cloud run.
