# Chaim Account Audit
Slack slash command to output account information.

It should detail the account name, number and owners.

It should list each user that has chaim access, with their respective roles
ordered by level.

The users should be listed in one of 3 groupings: regular, intermittent and
never used chaim (in the last 2 months).

## Install

### dev
```
poetry install
echo pymysql >requirements.txt
AWS_PROFILE=sadmin poetry run chalice deploy --stage=dev
```
Create a slash command within the `chaim` slack application at
https://api.slack.com/apps/A8N24EJG4/slash-commands that points to
the api gateway url that the `chalice` command, above, provides.

Log groups will be called `/aws/lambda/chaimaccountaudit-dev`
and `/aws/lambda/chaimaccountaudit-dev-doSNSReq`. Set both of these
to expire within 1 week.

### prod
```
AWS_PROFILE=sadmin poetry run chalice deploy --stage=prod
```

