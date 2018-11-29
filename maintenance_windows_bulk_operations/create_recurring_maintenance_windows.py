#!/usr/bin/env python

# Python script to create recurring maintenance windows in PagerDuty

import argparse
import pdpyras
import sys
import json
import dateutil.parser as dateparser
from datetime import datetime, timedelta


def create_recurring_maintenance_windows(args):
    sref = lambda s: {'type': 'service_reference', 'id':s}
    session = pdpyras.APISession(args.api_key, default_from=args.requester)
    start_date = dateparser.parse(args.first_maint_window_date)
    end_date = dateparser.parse(args.first_maint_window_date) + \
        timedelta(minutes=args.duration_minutes)
    for iter in range(1, args.num_repetitions, 1):
        start_date = start_date + timedelta(hours=args.period_hours)
        end_date = end_date + timedelta(hours=args.period_hours)
        print("Creating a %d-minute maintenance window starting %s."%(
            args.duration_minutes, start_date))
        if args.dry_run:
            continue
        try:
            mw = session.rpost('maintenance_windows', json={
                'type': 'maintenance_window',
                'start_time':start_date.isoformat(),
                'end_time':end_date.isoformat(),
                'description':args.description,
                'services':[sref(s_id) for s_id in args.service_ids]
            })
        except pdpyras.PDClientError as e:
            msg = "API Error: "
            if e.response is not None:
                msg += "HTTP %d: %s"%(e.response.status_code, e.response.text)
            print(msg)
    print("(Note: no maintenance windows actually created because -n/--dry-run "
        "was given)")
def main():
    desc = "Create a series of recurring maintenance windows."
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument('-k', '--api-key', required=True, help="A REST API key")
    helptxt = "User login email address of the PagerDuty user to record as "\
        "the agent who created the maintenance window."
    ap.add_argument('-r', '--requester', required=True, help=helptxt)
    helptxt = "Service ID(s) for which to create the maintenance windows. "\
        "Note, this may be given multiple times to specify more than one "\
        "service."
    ap.add_argument('-s', '--service', default=[], action='append',
        dest='service_ids', help=helptxt, required=True)
    helptxt = "Date of the first maintenance window in the series. It must be "\
        "formatted as valid ISO8601, i.e. 2018-10-19T17:45:00-0700"
    ap.add_argument('-t', '--date', required=True,
        dest='first_maint_window_date', help=helptxt)
    helptxt = "Description of the maintenance window to create."
    ap.add_argument('-d', '--description', required=True, help=helptxt)
    helptxt = "Duration of the maintenance window in minutes"
    ap.add_argument('-l', '--duration', required=True, dest='duration_minutes',
        type=int, help=helptxt)
    helptxt = "Number of hours between the start of each successive "\
        "maintenance window"
    ap.add_argument('-p', '--period', required=True, dest='period_hours',
        type=int, help=helptxt)
    helptxt = "Total number of maintenance windows to create"
    ap.add_argument('-m', '--number', default=1, dest='num_repetitions',
        type=int, help=helptxt)
    ap.add_argument('-n', '--dry-run', default=False, action='store_true',
        help="Don't perform any action; instead, show the maintenance windows "
        "that would be created.")
    args = ap.parse_args()

    create_recurring_maintenance_windows(args)

if __name__ == '__main__':
    main()
