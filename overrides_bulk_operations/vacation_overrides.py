#!/usr/bin/env python
import argparse
import json
import requests
import sys
import pdpyras

def find_shifts(session, vacationing_user, start, end, schedule_ids):
    """Find all on-call shifts on the specified schedules 
    between `since` and `until`"""
    params = {"since": start, "until": end}
    shifts = {} # Looks like: {(start, end): schedule_id}
    get_schedule = lambda sid: session.rget('/schedules/'+sid, params=params)
    schedules = [get_schedule(sid) for sid in schedule_ids]
    for schedule in schedules:
        for shift in schedule["final_schedule"]["rendered_schedule_entries"]:
            if shift["user"]["id"] == vacationing_user:
                print("Found shift for vacationing user from %s to %s"%(
                    shift["start"], shift["end"]))
                shifts[(shift["start"], shift["end"])] = schedule
    return shifts

def create_overrides():
    """For shift in find_shifts(), create an override to replace vacationing_user with replacement_user."""
    ap = argparse.ArgumentParser(description="For a given user going on "
        "vacation, and another given user who will fill their shoes while "
        "away, create overrides on all the vacationing user's schedules, such "
        "that the replacement user covers all the shifts that the vacationing "
        "user will be gone.")
    ap.add_argument('-v', '--vacationer', required=True, help="Login email "
        "address of the user who is going on vacation.")
    ap.add_argument('-u', '--substitute', required=True, help="Login email "
        "address of the user who is covering the shifts of the vacationing "
        "user.")
    ap.add_argument('-k', '--api-key', required=True, help="PagerDuty REST API "
        "key to use for operations.")
    ap.add_argument('-s', '--start', required=True, help="Start date of the "
        "vacation.")
    ap.add_argument('-e', '--end', required=True, help="End date of the "
        "vacation.")
    ap.add_argument('-c' , '--schedules', default=[], action='append',
        help="IDs of schedules in which to create overrides. If unspecified, "
        "all schedules will be included.")

    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    vacationing_user = session.find('users', args.vacationer, attribute='email')
    replacement_user = session.find('users', args.substitute, attribute='email')
    if None in (vacationing_user, replacement_user):
        print("Invalid login email specified for the vacationing user and/or "
            "substitute user.")
        return
    schedules = args.schedules
    if not args.schedules:
        print("Getting schedules...")
        schedules = [s['id'] for s in session.iter_all('schedules')]
    print("Looking for shifts that will require coverage...")
    shifts = find_shifts(session, vacationing_user['id'], args.start, args.end,
        schedules)

    for dates, schedule in shifts.items():
        start, end = dates
        print("Creating override on schedule %s (%s) from %s to %s..."%(
            schedule['id'], schedule['summary'], start, end))
        create_response = session.post('/schedules/%s/overrides'%schedule['id'],
            json={'override': {
                "start": start,
                "end": end,
                "user": {
                    "id": replacement_user['id'],
                    "type": "user_reference" 
                }
            }}
        )
        if not create_response.ok:
            message = "HTTP error: %d"%e.response.status_code
            print("Error creating override; "+message)
            continue
        print("Success.")

if __name__ == "__main__":
    create_overrides()
