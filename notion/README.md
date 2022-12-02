# User Status Table

## Overview

The User Status Table is a table in Notion where we sync parts of the data from
FHIR to. The purpose is for the back-officers to keep track of the records for
delivery and such without the need to access FHIR directly.

[Here](https://www.notion.so/umed-group/User-Status-Table-1f05480e48f64dc0991f3d11341fc738)
is the list of all the tables we have.

## Prerequisite

You need to retrieve the keys for `PubSub` integration conntection in Notion,
mainly `PubSubDev`, `PubSubStg`, and `PubSubProd`.

Ask in #development channel for access to the keys. Let's call this key
`pubsub-key` for this document.

## Procedures

### Update the headers

First, create a PR to update the `user-status-table` fields in this folder.

Once the PR is approved and merged, update the tables using the
[Notion API](https://developers.notion.com/reference/intro). Do each of the
following procedures through `dev`, `stg` and then `prod`.

First, create a file named `notion-api-key` with the content of the key above,
then export it to a environment variable:
```shell
touch notion-api-key
export NOTION_API_KEY=$(cat notion-api-key)
```

First, make sure that the key is correct by calling the
[retrieve database API](https://developers.notion.com/reference/retrieve-a-database):
```shell
# dev
curl 'https://api.notion.com/v1/databases/472e78832de34dcb833fff958972092a' \
  -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
  -H 'Notion-Version: 2022-06-28'
# stg
curl 'https://api.notion.com/v1/databases/3150ef13cf0748229a79f381430f1756' \
  -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
  -H 'Notion-Version: 2022-06-28'
# prod
curl 'https://api.notion.com/v1/databases/ca3627a5ace34e0fb0817c7cec354d71' \
  -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
  -H 'Notion-Version: 2022-06-28'
```

Once you have confirmed the call is successful, then use
[update database API](https://developers.notion.com/reference/update-a-database).
See [this guide](https://developers.notion.com/reference/update-property-schema-object)
on how to update the fields properly (adding/removing fields)::
```shell
# dev
curl --location --request PATCH 'https://api.notion.com/v1/databases/472e78832de34dcb833fff958972092a' \
--header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
--header 'Content-Type: application/json' \
--header 'Notion-Version: 2022-06-28' \
--data @user-status-table-dev.json
# stg
curl --location --request PATCH 'https://api.notion.com/v1/databases/3150ef13cf0748229a79f381430f1756' \
--header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
--header 'Content-Type: application/json' \
--header 'Notion-Version: 2022-06-28' \
--data @user-status-table-stg.json
# prod
curl --location --request PATCH 'https://api.notion.com/v1/databases/ca3627a5ace34e0fb0817c7cec354d71' \
--header 'Authorization: Bearer '"$NOTION_API_KEY"'' \
--header 'Content-Type: application/json' \
--header 'Notion-Version: 2022-06-28' \
--data @user-status-table-prod.json
```

## Resources

[Design](https://www.notion.so/umed-group/Notion-Database-Sync-Design-1dea60b5e8bd4d55b2e13ac63a3418f6)
[Notion API](https://developers.notion.com/reference/intro)
