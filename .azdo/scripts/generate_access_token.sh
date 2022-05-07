#!/bin/bash
set -e

base64var() {
    printf "$1" | base64stream
}

base64stream() {
    base64 | tr '/+' '_-' | tr -d '=\n'
}

key_json_file="$1"
scope="$2"

private_key=$(jq -r .private_key $key_json_file)
sa_email=$(jq -r .client_email $key_json_file)

header='{"alg":"RS256","typ":"JWT"}'
claim=$(cat <<EOF | jq -c .
  {
    "iss": "$sa_email",
    "scope": "$scope",
    "aud": "https://www.googleapis.com/oauth2/v4/token",
    "exp": $(($(date +%s) + 300)),
    "iat": $(date +%s)
  }
EOF
)
request_body="$(base64var "$header").$(base64var "$claim")"
signature=$(openssl dgst -sha256 -sign <(echo "$private_key") <(printf "$request_body") | base64stream)

jwt_token="$request_body.$signature"

access_token=$(curl -s -X POST https://oauth2.googleapis.com/token \
    --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer' \
    --data-urlencode "assertion=$jwt_token" \
    | jq -r .access_token)

echo "##vso[task.setvariable variable=access_token;issecret=true;isOutput=true]$access_token"
