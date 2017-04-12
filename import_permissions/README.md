# Import custom permissions from a CSV file

This script allows you to set custom PagerDuty user permissions en masse using a CSV file. A certain format must be adhered to in the input file.

## Format and validation

The input CSV file must contain the following columns:

**user email address, permission level, object type, object name**

The following assumptions are made:

1. The email address uniquely identifies a user.
1. The object type must be one of: `escalation_policy`, `schedule`, `service`, `team`
1. Objects of a given type, i.e. escalation policies or services, each have names that are unique to that type.
1. The permission level must be one of several valid types: 
  - `manager`: full standard user access to objects, i.e. modification of settings and creation of new objects.
  - `responder`: read-only access to most objects; and can acknowledge/resolve incidents.
  - `observer`: can only view objects and recevie notifications; a stakeholder.

```
email
```

## A note on API calls 

This script makes calls to `/users/{id}/roles`, an API endpoint that has not yet been formally published as part of the public REST API.

As such, this endpoint may be subject to change, in which case this script will be changed.
