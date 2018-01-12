#!/usr/bin/env python3

import argparse
import csv
import requests

def main():
    parser = argparse.ArgumentParser(description="Deletes overrides listed "\
        "in a CSV file. The first column should be the schedule ID and the "\
        "second should be the override ID.")
    parser.add_argument('-k', '--api-key', type=str, required=True, 
        dest='api_key', help="REST API key")
    parser.add_argument('-f', '--csv-file', type=argparse.FileType('r'),
        dest="csv_file", help="Path to input CSV file. Data should begin in "\
        "the very first row; no column names.")
    args = parser.parse_args()

    for schedule_id, override_id in csv.reader(args.csv_file):
        requests.delete(
            'https://api.pagerduty.com/schedules/{0}/overrides/{1}'.format(
                schedule_id, override_id
            ),
            headers = {
                'Authorization': 'Token token='+args.api_key,
            }
        )


if __name__ == '__main__':
    main()
   
