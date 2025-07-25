#!/usr/bin/env python

# PagerDuty Support asset: mass_update_incidents

import argparse
import requests
import sys
import json
from datetime import date
import pprint

import pagerduty
import time

# Default parameters:
PARAMETERS = {
    'exclude': ['escalation_policies', 'impacted_services', 'pending_actions', 'last_status_change_by', 'responders',
                'alert_grouping', 'conference_bridges']
}
MAX_INCIDENTS = 10000  # Maximum number of incidents to retrieve in one request, based on Python-Pagerduty SDK limits.


def mass_update_incidents(args):
    session = pagerduty.RestApiV2Client(args.api_key, default_from=args.requester_email)
    session.headers.update({"X-SOURCE-SCRIPT": "public-support-scripts/mass_update_incidents"})

    if args.user_id:
        PARAMETERS['user_ids[]'] = args.user_id.split(',')
        print("Acting on incidents assigned to user(s): " + args.user_id)
    if args.service_id:
        PARAMETERS['service_ids[]'] = args.service_id.split(',')
        print("Acting on incidents corresponding to service ID(s): " +
              args.service_id)
    if args.action == 'resolve':
        PARAMETERS['statuses[]'] = ['triggered', 'acknowledged']
        print("Resolving incidents")
    elif args.action == 'acknowledge':
        PARAMETERS['statuses[]'] = ['triggered']
        print("Acknowledging incidents")
    if args.date_range is not None:
        sinceuntil = args.date_range.split(',')
        if len(sinceuntil) != 2:
            raise ValueError("Date range must be two ISO8601-formatted time "
                             "stamps separated by a comma.")
        PARAMETERS['since'] = sinceuntil[0]
        PARAMETERS['until'] = sinceuntil[1]
        print("Getting incidents for date range: " + " to ".join(sinceuntil))
    else:
        PARAMETERS['date_range'] = 'all'
        print("Getting incidents of all time")
    print("Parameters: " + str(PARAMETERS))
    if args.incident_id:
        PARAMETERS['incident_ids[]'] = args.incident_id.split(',')
        if len(PARAMETERS['incident_ids[]']) > MAX_INCIDENTS:
            raise ValueError(
                f"You can only update a maximum of {MAX_INCIDENTS} incidents at a time. Received list of {len(PARAMETERS['incident_ids[]'])} incidents.")
    try:
        if args.incident_id:
            raw_incidents = args.incident_id.split(',')
            incidents = []
            for raw_incident in raw_incidents:
                incidents.append({"id": raw_incident})
            print("Acting on incidents corresponding to incident ID(s): " +
                  args.incident_id)
        else:
            print("Please be patient as this can take a while for large volumes "
                  "of incidents.")
            incidents = session.list_all('incidents', params=PARAMETERS)
        for incident in incidents:
            print("* Incident {}: {}".format(incident['id'], args.action))
            if args.dry_run:
                continue
            time.sleep(0.25)
            self_url = f"https://api.pagerduty.com/incidents/{incident['id']}"
            session.rput(self_url, json={
                'type': 'incident_reference',
                'status': '{0}d'.format(args.action),  # acknowledged or resolved
            })
    except pagerduty.Error as e:
        if e.response is not None:
            print(e.response.text)
        raise e


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mass ack or resolve incidents "
                                             "either corresponding to a given service, or assigned to a given "
                                             "user. Note, if you are trying to update over 10k incidents at a "
                                             "time, you should set the --date-range argument to a lesser interval "
                                             "of time and then run this script multiple times with a different "
                                             "interval each time until the desired range of time is covered.")
    ap.add_argument('-d', '--date-range', default=None, help="Only act on "
                                                             "incidents within a date range. Must be a pair of ISO8601-formatted "
                                                             "time stamps, separated by a comma, representing the beginning (since) "
                                                             "and end (until) of the date range. By default, incidents of all time "
                                                             "will be updated.")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-n', '--dry-run', default=False, action='store_true',
                    help="Do not perform the actions but show what will happen.")
    ap.add_argument('-i', '--incident-id', default=None, help="Id of the "
                                                              "incident, or comma separated list of incidents to be updated")
    ap.add_argument('-s', '--service-id', default=None, help="ID of the "
                                                             "service, or comma-separated list of services, for which incidents "
                                                             "should be updated; leave blank to match all services.")
    ap.add_argument('-u', '--user-id', default=None, help="ID of user, "
                                                          "or comma-separated list of users, whose assigned incidents should be "
                                                          "included in the action. Leave blank to match incidents for all users.")
    ap.add_argument('-a', '--action', default='resolve', choices=['acknowledge',
                                                                  'resolve'],
                    help="Action to take on incidents en masse")
    ap.add_argument('-e', '--requester-email', required=True, help="Email "
                                                                   "address of the user who will be marked as performing the actions.")
    args = ap.parse_args()
    mass_update_incidents(args)


if __name__ == '__main__':
    sys.exit(main())
