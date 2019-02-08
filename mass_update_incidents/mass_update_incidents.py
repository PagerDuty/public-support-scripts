#!/usr/bin/python

import argparse
import requests
import sys
import json
from datetime import date
import pprint

import pdpyras

# If you are trying to update over 10,000 incidents at a time, use the `since`,`until`, and `time_zone`
# parameters and comment out the `date_range` parameter
PARAMETERS = {
    'is_overview': 'true',
    'date_range': 'all'
    # 'since': '', 
    # 'until': '',
    # 'time_zone': `UTC` 
}

def mass_update_incidents(args):
    session = pdpyras.APISession(args.api_key,
        default_from=args.requester_email)
    if args.user_id:
        PARAMETERS['user_ids[]'] = args.user_id.split(',')
    if args.service_id:
        PARAMETERS['service_ids[]'] = args.service_id.split(',')
    if args.action == 'resolve':
        PARAMETERS['statuses[]'] = ['triggered', 'acknowledged']
    elif args.action == 'acknowledge':
        PARAMETERS['statuses[]'] = ['triggered']
    
    try:
        for incident in session.list_all('incidents', params=PARAMETERS):
            session.rput(incident['self'], json={
                'type': 'incident_reference',
                'id': incident['id'],
                'status': '{0}d'.format(args.action), # acknowledged or resolved
            })
    except pdpyras.PDClientError as e:
        if e.response is not None:
            print(e.response.text)
        raise e        

def main(argv=None):
    ap = argparse.ArgumentParser(description="Mass ack or resolve incidents "
        "either corresponding to a given service, or assigned to a given "
        "user.")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-s', '--service-id', default=None, help="ID of the "
        "service, or comma-separated list of services, for which incidents "
        "should be updated; leave blank to match all services.")
    ap.add_argument('-u', '--user-id', default=None, help="ID of user, "
        "or comma-separated list of users, whose assigned incidents should be "
        "included in the action. Leave blank to match incidents for all users.")
    ap.add_argument('-a', '--action', default='resolve', choices=['acknowldege',
        'resolve'], help="Action to take on incidents en masse")
    ap.add_argument('-e', '--requester-email', required=True, help="Email "
        "address of the user who will be marked as performing the actions.")
    args = ap.parse_args()
    mass_update_incidents(args)

if __name__=='__main__':
    sys.exit(main())
