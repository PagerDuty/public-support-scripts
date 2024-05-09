#!/usr/bin/env python3

# this script retrieves all user role audit records for a given date range
# the endpoint for audit records is https://api.pagerduty.com/audit/records

import argparse
import pdpyras
from dateutil import parser, relativedelta
from datetime import datetime, timezone

user_tiers = {
    'full_user': 'Full User',
    'stakeholder': 'Stakeholer'
}

user_roles = {
    'owner': 'Owner',
    'admin': 'Global Admin',
    'user': 'Manager',
    'limited_user': 'Responder',
    'observer': 'Observer',
    'restricted_access': 'Restricted Access',
    'read_only_limited_user': 'Limited Stakeholder',
    'read_only_user': 'Stakeholder'
}

user_role_to_tier = {
    'owner': 'full_user',
    'admin': 'full_user',
    'user': 'full_user',
    'limited_user': 'full_user',
    'observer': 'full_user',
    'restricted_access': 'full_user',
    'read_only_limited_user': 'stakeholder',
    'read_only_user': 'stakeholder'
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
        params['actions[]'] = 'update'
    return params

def print_changes(changes, audit_tier_changes):
    format_string = '%(date)-25s %(id)-10s %(summary)-20.20s %(before_value)-20s %(value)-20s %(actor_id)-10s %(actor_type)-10s %(actor_summary)-20.20s'
    table_max_width = 145

    # Print the header row before sorting the actual changes
    print(format_string % changes[0])
    print(''.join(['-' for _ in range(table_max_width)]))

    # Pop the header row
    changes.pop(0)
    changes = sorted(changes, key=lambda rc: rc['date'])

    # Get human readable representations of the API role/tier values
    for change in changes:
        if audit_tier_changes:
            change['value'] = user_tiers[change['value']]
            change['before_value'] = user_tiers[change['before_value']]
        else:
            change['value'] = user_roles[change['value']]
            change['before_value'] = user_roles[change['before_value']]

        print(format_string % change)

def header_row(audit_tier_changes):
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

    if audit_tier_changes:
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
        'actor_summary': actor['summary'] if 'summary' in actor else ''
    }

def get_role_changes(record):
    # The user specific audit endpoint will sometimes send us `create` records, discard them.
    if record['action'] != 'update':
        return []

    # `details` and `fields` can both be null according to the API docs.
    field_changes = record.get('details', {}).get('fields', [])
    role_changes = filter(lambda fc: fc['name'] == 'role', field_changes)

    def hydarate_role_change(role_change):
        role_change.update(record['root_resource'])
        role_change.update(get_record_actor(record))
        role_change['date'] = record['execution_time']
        return role_change

    return list(map(hydarate_role_change, role_changes))

def get_role_tier_changes(role_changes):
    tier_changes = []
    for role_change in role_changes:
        role_change['value'] = user_role_to_tier[role_change['value']]
        role_change['before_value'] = user_role_to_tier[role_change['before_value']]
        if role_change['value'] != role_change['before_value']:
            tier_changes.append(role_change)

    return tier_changes

def chunk_date_range(since, until):
    # Mirror the default of the audit APIs, get records for the last 24 hours
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

def main(since, until, user_id, audit_tier_changes, session):
    try:
        role_changes = []
        chunked_date_range = chunk_date_range(since, until)
        for since, until in chunked_date_range:
            for record in session.iter_cursor(get_api_path(user_id), params=get_api_params(since, until, user_id)):
                record_role_changes = get_role_changes(record)
                role_changes += record_role_changes

        header = header_row(audit_tier_changes)

        changes = get_role_tier_changes(role_changes) if audit_tier_changes else role_changes

        if len(changes):
            print_changes(header + changes, audit_tier_changes)
        else:
            print(f'No {"tier" if audit_tier_changes else "role"} changes found.')

    except pdpyras.PDClientError as e:
        print('Could not get user role change audit records')
        raise e

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Prints all user role or tier changes between the given dates')
    ap.add_argument('-k', '--api-key', required=True, help='REST API key')
    ap.add_argument('-s', '--since', required=False, help='start date')
    ap.add_argument('-u', '--until', required=False, help='end date')
    ap.add_argument('-i', '--user-id', required=False, help='Filter results to a single user ID')
    ap.add_argument('-t', '--audit-tier-changes', action='store_true', help='Audit user role tier changes')
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)

    main(
        args.since,
        args.until,
        args.user_id,
        args.audit_tier_changes,
        session
    )
