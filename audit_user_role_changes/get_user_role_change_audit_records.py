# !/usr/bin/env python

# this script retrieves all user role audit records for a given date range
# the endpoint for audit records is https://api.pagerduty.com/audit/records

import argparse
import pdpyras
import sys

def get_user_role_change_audit_records(since, until, session):
    try:
        sys.stdout.write("User Role Change Audit Records:\n")
        for record in session.iter_cursor('audit/records', params={'since': since, 'until': until, 'actions[]': 'update', 'root_resource_types[]': 'users'}):
            if record['details']['fields'][0]['name'] == 'role':
                sys.stdout.write("User: {}\n".format(record['details']['resource']['summary']))
                sys.stdout.write("Role change from: {} to {}\n".format(record['details']['fields'][0]['before_value'], record['details']['fields'][0]['value']))
                sys.stdout.write("-----\n")
    except pdpyras.PDClientError as e:
        print("Could not get user role change audit records")
        raise e


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves all user role change audit records between the given dates")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-s', '--since', required=False, help="start date", dest='since')
    ap.add_argument('-u', '--until', required=False, help="end date", dest='until')
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    get_user_role_change_audit_records(args.since, args.until, session)
