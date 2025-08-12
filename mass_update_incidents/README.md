# Mass Update Incidents

Performs status updates (acknowledge or resolve) in bulk to an almost arbitrary
number (maximum: 10k at a time) of incidents that all have an assignee user or
service (or both) in commmon. The script processes incidents in batches of 100 with rate limiting.

If operating on more than 10k incidents: it is recommended that you run the
script several times by constraining it to a service ID each time, and/or
requesting a time range by setting the `-d/--date-range` option.

## Script Arguments

Below are the arguments for the script.

`-d` : Only act on incidents within a date range. Must be a pair of ISO8601-formatted time stamps, separated by a comma, representing the beginning (since) and end (until) of the date range. By default, incidents of all time will be updated.

`-k` : REST API key. Follow this [guide](https://support.pagerduty.com/docs/api-access-keys) if you need to know how to generate a new API key.

`-n` : Do not perform the actions but show what will happen.

`-s` : ID of the service, or comma-separated list of services, for which incidents should be updated; leave blank to match all services.

`-i` : ID of the incident, or comma-separated list of incidents, for which incidents should be updated

`-u` : ID of user, or comma-separated list of users, whose assigned incidents should be included in the action. Leave blank to match incidents for all users.

`-a` : default=`resolve`, Action to take on incidents (acknowledge/resolve)

`-e` : Email address of the user who will be marked as performing the actions.

## Examples

The below example will only dry run the script and no actions will be taken to resolve/acknowledge the incidents.

```
python3 mass_update_incidents.py -k API-KEY_HERE -u USER-ID -a acknowledge -e YOUR-EMAIL -n
```
The below example will acknowledge all the incidents assigned to a user.

```
python3 mass_update_incidents.py -k API-KEY_HERE -u USER-ID -a acknowledge -e YOUR-EMAIL
```

The below example will resolve all incidents that belongs to a service.

```
python3 mass_update_incidents.py -k API-KEY_HERE -s SERVICE-ID -a resolve -e YOUR-EMAIL
```

The below example will resolve all incidents with the associated incident ID(s) 

```
python3 mass_update_incidents.py -k API-KEY_HERE -i INCIDENT-ID -a resolve -e YOUR-EMAIL
```


The below example will resolve all incidents assigned to both user1 and user2.

```
python3 mass_update_incidents.py -k API-KEY_HERE -s USER1-ID,USER2_ID -a resolve -e YOUR-EMAIL
```
