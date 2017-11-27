#!/usr/bin/python

import requests
import sys
import json
from datetime import date
import pprint

# Your PagerDuty REST API key (v2) - must be full access
auth_token = 'API_KEY_HERE'

# The PagerDuty service id (leave blank for all services or comma separate
# multiple services)
pd_service = ''

# Action to take (must be one of 'acknowledge' or 'resolve')
incident_action = 'resolve'

# Email address of the user who will be marked as performing these actions
incident_action_email = ''

# User ID for which inidents need to be resolved or acked. Leave blank to
# operate on all incidents, or use a comma-separated list for multiple.
incident_assignee_userid = ''

HEADERS = {
    'Authorization': 'Token token={0}'.format(auth_token),
    'Content-type': 'application/json',
    'Accept': 'application/vnd.pagerduty+json;version=2',
}

PARAMETERS = {
    'is_overview': 'true',
    'date_range': 'all',
    'limit': 100,
}

if incident_action == 'resolve':
    PARAMETERS['status'] = 'triggered,acknowledged'
elif incident_action == 'acknowledge':
    PARAMETERS['status'] = 'triggered'
if incident_assignee_userid:
    PARAMETERS['user_ids[]'] = incident_assignee_userid.split(',')
if pd_service:
    PARAMETERS['service_ids[]'] = pd_service.split(',')

def mass_update_incidents():
    offset = 0
    while True:
        PARAMETERS['offset'] = offset
        offset += PARAMETERS['limit']
        incidents = get_open_incidents(PARAMETERS)

        if len(incidents) == 0:
            break

        for incident in incidents:
            ack_or_resolve_incident(incident['id'], incident_action,
                incident_action_email)

def get_open_incidents(params):
    incidents = requests.get(
        'https://api.pagerduty.com/incidents',
        headers=HEADERS,
        params=params
    )

    if incidents.status_code != 200:
        print("Error getting incidents: {0}".format(incidents.status_code))
        print("Response: {0}".format(incidents.text))

    return incidents.json()['incidents']

def ack_or_resolve_incident(incident, action, requester):
    headers = dict(HEADERS)
    headers['From'] = requester
    incidents = requests.put(
        'https://api.pagerduty.com/incidents/{0}'.format(incident),
        headers=headers,
        json={
            'incident': {
                'type': 'incident_reference',
                'id': incident,
                'status': '{0}d'.format(action), # acknowledged or resolved
            }
        }
    )

    if incidents.status_code != 200:
        print("Error updating incident: {0}".format(incidents.status_code))
        print("Response: {0}".format(incidents.text))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    mass_update_incidents()

if __name__=='__main__':
    sys.exit(main())
