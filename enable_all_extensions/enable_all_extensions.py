#!/usr/bin/env python3

import requests
import argparse
import json
import sys
import re
import csv


class Extension_Enabler:
    def __init__(self, args):
        self.baseurl = f'https://api.pagerduty.com/extensions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "From": args.requester_email,
            "Authorization": f"Token token={args.api_key}"
        }

    def enable(self, extension):
        ex_id = extension['id']
        ex_type = extension['extension_schema']['summary']
        ex_name = extension['summary']
        link = (extension['extension_objects'][0]['html_url'] 
                + '/integrations?service_profile=1')
        link = link.replace('/service-directory', '/services')
        url = f'https://api.pagerduty.com/extensions/{ex_id}/enable'
        response = requests.post(url, headers=self.headers)

        if response.status_code >= 200 and response.status_code < 300:
            json = response.json()
            print(f"extension {ex_id} {ex_type} '{ex_name}' was reenabled")
        else:
            print(f"ERROR: {ex_id} {ex_type} '{ex_name}' was not reenabled\n"
                  f"       Received status code {response.status_code}\n"
                  f"       Link: {link}")

    def enable_all_extensions(self):
        more = True
        offset = 0
        results = self.retrieve_all_extensions()

        self.validate_API_response(results)
        subdomain = results[0]['extension_objects'][0].get('html_url', 
            'domainless').replace("/", "").split(":")[1].split(".")[0]
        
        print(f"{len(results)} extensions found on account '{subdomain}'")
        print(f"Enabling all disabled extensions...")

        count = 0
        for extension in results:
            if extension['temporarily_disabled']:
                self.enable(extension)
                count += 1

        if count == 0:
            print(f"All extensions on '{subdomain}' were already enabled.")

        print(" --- Script completed. ---")

    def retrieve_all_extensions(self):
        more = True
        offset = 0
        results = []

        while more:
            url = (self.baseurl + "?include%5B%5D=temporarily_disabled"
                                + f"&limit=100&offset={offset}")
            response = requests.get(url, headers=self.headers).json()
            results.extend(response['extensions'])

            if response['more'] == False:
                more = False

            offset = offset + 100

        return results

    def validate_API_response(self, results):
        if len(results) == 0:
            print("The API returned no extensions for the account.")
            sys.exit()
        else:
            ext = results[0]
            if ('extension_objects' not in ext or 'summary' not in ext or 
                    'id' not in ext or 'extension_schema' not in ext or 
                    'summary' not in ext['extension_schema'] or 
                    'html_url' not in ext['extension_objects'][0]):
                print('The PagerDuty REST API is returning a format different '
                      'from what this script expects.  Feel free to reach out '
                      'to support@pagerduty.com to let Tier 2 support know '
                      'that this script will need to be updated.')
                sys.exit()


def main():
    ap = argparse.ArgumentParser(
        description="Reenable all temporarily disabled extensions on an account"
    )
    ap.add_argument("-k",
        "--api-key",
        required=True,
        help="REST API key"
    )
    ap.add_argument(
        "-e",
        "--requester-email",
        required=True,
        help="Email address of the user who will be performing the actions",
    )
    args = ap.parse_args()

    Extension_Enabler(args).enable_all_extensions()


if __name__ == "__main__":
    sys.exit(main())
