#!/usr/bin/env python3

# PagerDuty Support asset: mass_update_incidents

import argparse
import requests
import sys
import json
from datetime import date, datetime, timedelta
from dateutil.parser import parse, ParserError
import pprint

import pdpyras

# Default parameters:
PARAMETERS = {
    'is_overview': 'true',
    # 'since': '', 
    # 'until': '',
    # 'time_zone': `UTC` 
}

def mass_update_incidents(args):
    session = pdpyras.APISession(args.api_key,
        default_from=args.requester_email)
    hour_slices = []
    if args.user_id:
        PARAMETERS['user_ids[]'] = args.user_id.split(',')
        print("Acting on incidents assigned to user(s): "+args.user_id)
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
    if args.date_range is None:
        PARAMETERS['date_range'] = 'all'
        print("Getting incidents of all time")
    else:
        sinceuntil = args.date_range.split(',')
        if len(sinceuntil) != 2:
            raise ValueError("Date range must be two ISO8601-formatted time "
                "stamps separated by a comma.")
        given_start_date = parse(sinceuntil[0])
        given_end_date = parse(sinceuntil[1])
        if given_end_date - given_start_date > timedelta(hours=1):
            hour_slices = hour_slicer(sinceuntil[0], sinceuntil[1])
        # else:
            # PARAMETERS['since'] = sinceuntil[0]
            # PARAMETERS['until'] = sinceuntil[1]
        print("Getting incidents for date range: "+" to ".join(sinceuntil))
    print("Parameters: "+str(PARAMETERS))
    print("Please be patient as this can take a while for large volumes "
        "of incidents.")
    # if 1hr slicing is not needed, then this for loop will be no-op
    for begin_date in hour_slices:
        print("Now retrieving a batch of incidents...")
        PARAMETERS['since'] = begin_date
        PARAMETERS['until'] = begin_date + timedelta(hours=1)
        incident_handler(session, args)
    # if sliced into hours, this performs one final sweep through the whole
    # range to catch stragglers
    incident_handler(session, args)

def hour_slicer(begin_time, end_time):
    date_range = []
    start_time = parse(begin_time)
    end_time = parse(end_time)
    while start_time < end_time:
        date_range.append(start_time)
        start_time = start_time + timedelta(hours=1)
    date_range.append(start_time)
    return date_range

def incident_handler(session, args):
    for incident in session.list_all('incidents', params=PARAMETERS):
        if args.dry_run:
            print("* Incident {}: {}".format(incident['id'], args.action))
            continue
        if args.title_filter is None:
            try:
                print("* Incident {}: {}".format(incident['id'], args.action))
                session.rput(incident['self'], json={
                    'type': 'incident_reference',
                    'id': incident['id'],
                    'status': '{0}d'.format(args.action),
                })
            except pdpyras.PDClientError as e:
                if e.response is not None:
                    print(e.response.text)
                # raise e
        else:
            if 'title' in incident.keys() and \
                args.title_filter in incident['title']:
                print("* Incident {}: {}".format(incident['id'], args.action))
                try:
                    session.rput(incident['self'], json={
                        'type': 'incident_reference',
                        'id': incident['id'],
                        'status': '{0}d'.format(args.action),
                    })
                except pdpyras.PDClientError as e:
                    if e.response is not None:
                        print(e.response.text)
                    # raise e

def main(argv=None):
    ap = argparse.ArgumentParser(description="Mass ack or resolve incidents "
        "either corresponding to a given service, or assigned to a given "
        "user. Note, if you are trying to update over 10k incidents at a "
        "time, you should use the --date-range argument instead. If the date "
        "range given is longer than 1 hour it will be batched into 1-hour "
        " slices.")
    ap.add_argument('-d', '--date-range', default=None, help="Only act on "
        "incidents within a date range. Must be a pair of ISO8601-formatted "
        "time stamps, separated by a comma, representing the beginning (since) "
        "and end (until) of the date range. By default, incidents of all time "
        "will be updated.")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-n', '--dry-run', default=False, action='store_true',
        help="Do not perform the actions but show what will happen.")
    ap.add_argument('-s', '--service-id', default=None, help="ID of the "
        "service, or comma-separated list of services, for which incidents "
        "should be updated; leave blank to match all services.")
    ap.add_argument('-u', '--user-id', default=None, help="ID of user, "
        "or comma-separated list of users, whose assigned incidents should be "
        "included in the action. Leave blank to match incidents for all users.")
    ap.add_argument('-a', '--action', default='resolve', choices=['acknowledge',
        'resolve'], help="Action to take on incidents en masse")
    ap.add_argument('-e', '--requester-email', required=True, help="Email "
        "address of the user who will be marked as performing the actions.")
    ap.add_argument('-t', '--title-filter', default=None, help="(Optional) "
        "string to search in the Title field of each Incident, to ensure only "
        "known types of incidents are handled.")
    args = ap.parse_args()
    mass_update_incidents(args)

if __name__=='__main__':
    sys.exit(main())
