#!/usr/bin/env python3

import requests
import argparse
import json
import sys
import re
import csv


def set_headers(args):
	api_key = args.api_key
	email = args.requester_email
	baseurl = f'https://api.pagerduty.com/extensions'
	headers = {
		"Content-Type": "application/json",
		"Accept": "application/vnd.pagerduty+json;version=2",
		"From": email,
		"Authorization": f"Token token={api_key}"
	}
	return headers, baseurl


def enable(extension, headers):
	ex_id = extension['id']
	ex_type = extension['extension_schema']['summary']
	ex_name = extension['summary']
	link = extension['extension_objects'][0]['html_url'] + '/integrations?service_profile=1'
	link = link.replace('/service-directory', '/services')
	url = f'https://api.pagerduty.com/extensions/{ex_id}/enable'
	response = requests.post(url, headers=headers)

	if response.status_code >= 200 and response.status_code < 300:
		json = response.json()
		print(f"extension {ex_id} {ex_type} '{ex_name}' was reenabled")
	else:
		print(f"ERROR: {ex_id} {ex_type} '{ex_name}' was not reenabled\n"
			f"       Received status code {response.status_code}\n"
			f"       Link: {link}")


def enable_all_extensions(args):
	more = True
	offset = 0
	results = []

	headers, baseurl = set_headers(args)

	while more:
		url = baseurl + f"?include%5B%5D=temporarily_disabled&limit=100&offset={offset}"
		response = requests.get(url, headers=headers).json()
		results.extend(response['extensions'])

		if response['more'] == False:
			more = False

		offset = offset + 100

	subdomain = results[0]['extension_objects'][0].get('html_url', 
		'domainless').replace("/", "").split(":")[1].split(".")[0]
	
	print(f"{len(results)} extensions found on account '{subdomain}'")
	print(f"Enabling all disabled extensions...")

	count = 0
	for extension in results:
		if extension['temporarily_disabled']:
			enable(extension, headers)
			count += 1

	if count == 0:
		print(f"All extensions on '{subdomain}' were already enabled.")

	print(" --- Script completed. ---")


def main(argv=None):
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

	enable_all_extensions(args)


if __name__ == "__main__":
	sys.exit(main())
