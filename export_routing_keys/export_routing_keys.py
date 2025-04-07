#!/usr/bin/env python

import argparse
import pagerduty
import sys
import csv
import re


def print_event_orchestrations(session, csvwriter, subdomain):
    for eo in session.iter_all('event_orchestrations'):
        url = "https://%s.pagerduty.com/event-orchestration/%s/integrations" % (subdomain, eo['id'])
        integrations = session.jget('event_orchestrations/%s/integrations' % eo['id'])

        for integration in integrations['integrations']:
            routing_key = integration['parameters']['routing_key']
            label = integration['label']
            csvwriter.writerow(['event_orchestration', routing_key, label, url])


def print_rulesets(session, csvwriter, subdomain):
    for ruleset in session.iter_all('rulesets'):
        for routing_key in ruleset['routing_keys']:
            url = "https://%s.pagerduty.com/rules/rulesets/%s" % (subdomain, ruleset['id'])
            label = ruleset['name']
            csvwriter.writerow(['global_ruleset', routing_key, label, url])


def print_service_integrations(session, csvwriter):
    for service in session.iter_all('services', {'include[]': ['integrations']}):
        for integration in service['integrations']:
            routing_key = None
            if 'integration_key' in integration:
                routing_key = integration['integration_key']
            elif 'integration_email' in integration:
                routing_key = integration['integration_email']

            if routing_key:
                label = integration['name']
                url = integration['html_url']
                csvwriter.writerow(['service_integration', routing_key, label, url])


def get_subdomain(session):
    users = session.jget('users')
    return re.match(r'https:\/\/(.*)\.pagerduty\.com.*/', users['users'][0]['html_url']).group(1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Generates a CSV of all routing keys and their resource URL")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-o', '--csv-file', required=False, help="Output CSV File")
    args = ap.parse_args()
    session = pagerduty.RestApiV2Client(args.api_key)

    output = open(args.csv_file, 'w', newline='') if args.csv_file else sys.stdout
    with output as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Integration Type', 'Routing Key', 'Name', 'Link'])

        subdomain = get_subdomain(session)
        print_service_integrations(session, csvwriter)
        print_event_orchestrations(session, csvwriter, subdomain)
        print_rulesets(session, csvwriter, subdomain)
