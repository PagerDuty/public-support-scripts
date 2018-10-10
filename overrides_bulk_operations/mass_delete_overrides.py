#!/usr/bin/env python3

import argparse
import csv
import requests
import pdpyras

def main():
    parser = argparse.ArgumentParser(description="Deletes overrides listed "\
        "in a CSV file. The first column should be the schedule ID and the "\
        "second should be the override ID. More columns can be included after "
        "the first.")
    parser.add_argument('-k', '--api-key', type=str, required=True, 
        dest='api_key', help="REST API key")
    parser.add_argument('-f', '--csv-file', type=argparse.FileType('r'),
        dest="csv_file", help="Path to input CSV file. Data should begin in "\
        "the very first row; no column names.")
    args = parser.parse_args()

    session = pdpyras.APISession(args.api_key)
    for row in csv.reader(args.csv_file):
        schedule_id, override_id = row[:2]
        try:
            session.rdelete('/schedules/%s/overrides/%s'%(
                schedule_id, override_id
            ))
            print("Deleted override "+override_id)
        except pdpyras.PDClientError as e:
            error = 'Network error'
            if e.response is not None:
                error = e.response.text
            print("Could not delete override %s; %s"%(override_id, error))
            continue

if __name__ == '__main__':
    main()
