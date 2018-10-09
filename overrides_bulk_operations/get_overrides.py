#!/usr/bin/env python3

import argparse
import csv
import requests
import pdpyras

def main():
    ap = argparse.ArgumentParser(description="Gets all overrides in a "
        "schedule and export to a CSV file. The first column of output will "
        "be the schedule ID and the second should be the override ID, and the "
        "third will be a column identifying the user and time.")
    ap.add_argument('-k', '--api-key', type=str, required=True, 
        dest='api_key', help="REST API key")
    ap.add_argument('-f', '--csv-file', type=argparse.FileType('w'),
        dest="csv_file", help="Output CSV file. Data will begin in the very "\
        "first row; no column names.")
    ap.add_argument('-s', '--start', required=True, help="Start date of search")
    ap.add_argument('-e', '--end', required=True, help="End date of search")
    ap.add_argument('-c' , '--schedules', default=[], action='append',
        help="IDs of schedules in which to find overrides. If unspecified, "
        "all schedules will be included.")

    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    window = {'since':args.start, 'until':args.end}
    writer = csv.writer(args.csv_file)
    schedules = args.schedules
    if not args.schedules:
        print("Getting schedules...")
        schedules = [s['id'] for s in session.iter_all('schedules')]

    for sid in schedules:
        for override in session.iter_all('/schedules/%s/overrides'%sid, 
                params=window):
            idtag = "%s: %s to %s"%(override['user']['summary'], 
                override['start'], override['end'])
            writer.writerow((sid, override['id'], idtag))

if __name__ == '__main__':
    main()
