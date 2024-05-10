#!/usr/bin/env python3

# this script retrieves all user role audit records for a given date range
# the endpoint for audit records is https://api.pagerduty.com/audit/records

import argparse
import csv
import json
import pdpyras
from datetime import datetime, timezone
from dateutil import parser, relativedelta
from tabulate import tabulate

user_roles = {
    'owner': 'Owner',
    'admin': 'Global Admin',
    'user': 'Manager',
    'limited_user': 'Responder',
    'observer': 'Observer',
    'restricted_access': 'Restricted Access',
    'read_only_limited_user': 'Limited Stakeholder',
    'read_only_user': 'Stakeholder',
    'none': 'None'
}

user_role_to_tier = {
    user_roles['owner']: 'Full User',
    user_roles['admin']: 'Full User',
    user_roles['user']: 'Full User',
    user_roles['limited_user']: 'Full User',
    user_roles['observer']: 'Full User',
    user_roles['restricted_access']: 'Full User',
    user_roles['read_only_limited_user']: 'Stakeholder',
    user_roles['read_only_user']: 'Stakeholder',
    user_roles['none']: 'None'
}

actor_types = {
    'user_reference': 'User',
    'app_reference': 'App',
    'api_key_reference': 'API Key',
}

def get_api_path(user_id):
    return f'users/{user_id}/audit/records' if user_id else 'audit/records'

def get_api_params(since, until, user_id):
    params={'since': since, 'until': until}
    if not user_id:
        params['root_resource_types[]'] = 'users'
    return params

def print_changes(changes, tier_changes):
    header = header_row(tier_changes)
    print(tabulate(header + changes, tablefmt='grid'))

def write_changes_to_csv(changes, tier_changes, filename):
    header = header_row(tier_changes)
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header[0].keys())
        writer.writerows(header + changes)

def header_row(tier_changes):
    header = {
            'date': 'Date',
            'id': 'User ID',
            'summary': 'User Name',
            'before_value': 'Role Before',
            'value': 'Role After',
            'actor_id': 'Actor ID',
            'actor_type': 'Actor Type',
            'actor_summary': 'Actor Summary'
        }

    if tier_changes:
        header.update({'before_value': 'Role Tier Before', 'value': 'Role Tier After'})

    return [header]

def get_record_actor(record):
    actors = record.get('actors', [])
    if not len(actors):
        return {
            'actor_type': '',
            'actor_id': '',
            'actor_summary': ''
        }

    actor = actors[0]
    return {
        'actor_type': actor_types[actor['type']],
        'actor_id': actor['id'],
        'actor_summary': actor.get('summary', '')
    }

def get_role_changes(record):
    # `details` and `fields` can both be null according to the API docs.
    field_changes = record.get('details', {}).get('fields', [])
    role_changes = filter(lambda fc: fc['name'] == 'role', field_changes)

    def format_role_change(role_change):
        role_change = {
            'id': record['root_resource']['id'],
            'summary': record['root_resource'].get('summary', ''),
            'value': user_roles[role_change.get('value', 'none')],
            'before_value': user_roles[role_change.get('before_value', 'none')],
            'date': record['execution_time']
        }
        role_change.update(get_record_actor(record))
        return role_change

    return list(map(format_role_change, role_changes))

def get_role_tier_changes(role_changes):
    tier_changes = []
    for role_change in role_changes:
        role_change['value'] = user_role_to_tier[role_change['value']]
        role_change['before_value'] = user_role_to_tier[role_change['before_value']]
        if role_change['value'] != role_change['before_value']:
            tier_changes.append(role_change)

    return tier_changes

def chunk_date_range(args):
    # Mirror the default of the audit APIs, get records for the last 24 hours
    since, until = args.since, args.until
    if not since or not until:
        now = datetime.now(timezone.utc)
        yesterday = now - relativedelta.relativedelta(hours=+24)
        yield (datetime.isoformat(yesterday), datetime.isoformat(now))
        return

    since = parser.isoparse(since)
    until = parser.isoparse(until)

    if since > until:
        raise 'Invalid date range'

    # Audit API requests have a date range limit of 31 days, so we
    # split the requested date range into 30 day chunks
    while True:
        next_since = since + relativedelta.relativedelta(days=+30)
        if next_since < until:
            yield (datetime.isoformat(since), datetime.isoformat(next_since))
            since = next_since
        else:
            yield (datetime.isoformat(since), datetime.isoformat(until))
            return

def main(args, session):
    user_id, tier_changes = args.user_id, args.tier_changes
    try:
        role_changes = []
        chunked_date_range = chunk_date_range(args)
        for since, until in chunked_date_range:
            for record in session.iter_cursor(get_api_path(user_id), params=get_api_params(since, until, user_id)):
                if args.show_all:
                    print(json.dumps(record))
                record_role_changes = get_role_changes(record)
                role_changes += record_role_changes

        changes = get_role_tier_changes(role_changes) if tier_changes else role_changes
        if len(changes):
            changes = sorted(changes, key=lambda rc: rc['date'])
            print_changes(changes, tier_changes)
            if args.filename:
                write_changes_to_csv(changes, tier_changes, args.filename)
        else:
            print(f'No {"tier" if tier_changes else "role"} changes found.')

    except pdpyras.PDClientError as e:
        print('Could not get user role change audit records')
        raise e

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Prints all user role or tier changes between the given dates')
    ap.add_argument('-k', '--api-key', required=True, help='REST API key')
    ap.add_argument('-s', '--since', required=False, help='Start of date range to search')
    ap.add_argument('-u', '--until', required=False, help='End of date range to search')
    ap.add_argument('-i', '--user-id', required=False, help='Filter results to a single user ID')
    ap.add_argument('-t', '--tier-changes', action='store_true', help='Get user role tier changes')
    ap.add_argument('-a', '--show-all', action='store_true', help='Prints all fetched user records in JSON format')
    ap.add_argument('-f', '--filename', required=False, help='Write results to a CSV file')
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)

    main(args, session)
