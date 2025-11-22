#!/usr/bin/env python3
#
# Copyright (c) 2025, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# PagerDuty Support asset: user_association_report
#
# Generates a report of PagerDuty users and their associations with schedules,
# escalation policies, teams, and open incidents. Identifies "orphan" users who
# are not associated with any operational resources.

import argparse
import csv
import json
import logging
import os
from datetime import datetime

from pdpyras import APISession

log = logging.getLogger('orphan_users_report')


class PagerDutyCache:
    """
    Caches all PagerDuty resources to minimize API calls.
    Fetches users, schedules, escalation policies, teams, and open incidents once.
    """

    def __init__(self, access_token, from_email):
        self.session = APISession(access_token, default_from=from_email)
        self._users = None
        self._schedules = None
        self._escalation_policies = None
        self._teams = None
        self._team_users = {}
        self._open_incidents = None
        self._user_incident_counts = {}

    def get_users(self):
        """Fetch and cache all users"""
        if self._users is None:
            log.info("Fetching all users...")
            print("Fetching all users. This may take a moment...")
            self._users = list(self.session.iter_all('users'))
            log.info("Found %d users", len(self._users))
        return self._users

    def get_schedules(self):
        """Fetch and cache all schedules with their user details"""
        if self._schedules is None:
            log.info("Fetching all schedules...")
            print("Fetching all schedules. This may take several minutes...")
            self._schedules = list(self.session.iter_all('schedules'))
            for schedule in self._schedules:
                schedule['details'] = self.session.rget(schedule.get('self'))
            log.info("Found %d schedules", len(self._schedules))
        return self._schedules

    def get_escalation_policies(self):
        """Fetch and cache all escalation policies"""
        if self._escalation_policies is None:
            log.info("Fetching all escalation policies...")
            print("Fetching all escalation policies. This may take a moment...")
            self._escalation_policies = list(self.session.iter_all('escalation_policies'))
            log.info("Found %d escalation policies", len(self._escalation_policies))
        return self._escalation_policies

    def get_teams(self):
        """Fetch and cache all teams"""
        if self._teams is None:
            log.info("Fetching all teams...")
            print("Fetching all teams. This may take a moment...")
            self._teams = list(self.session.iter_all('teams'))
            log.info("Found %d teams", len(self._teams))
        return self._teams

    def get_team_users(self, team_id):
        """Fetch and cache users for a specific team"""
        if team_id not in self._team_users:
            users = list(self.session.iter_all('users', params={'team_ids[]': team_id}))
            self._team_users[team_id] = [u['id'] for u in users]
        return self._team_users[team_id]

    def get_open_incidents(self):
        """Fetch and cache all open (triggered/acknowledged) incidents"""
        if self._open_incidents is None:
            log.info("Fetching all open incidents...")
            print("Fetching all open incidents. This may take a moment...")
            self._open_incidents = list(self.session.iter_all(
                'incidents',
                params={
                    'statuses[]': ['triggered', 'acknowledged'],
                    'date_range': 'all'
                }
            ))
            log.info("Found %d open incidents", len(self._open_incidents))
            self._build_user_incident_counts()
        return self._open_incidents

    def _build_user_incident_counts(self):
        """Build a mapping of user IDs to their open incident counts"""
        for incident in self._open_incidents:
            for assignment in incident.get('assignments', []):
                assignee = assignment.get('assignee', {})
                if assignee.get('type') in ('user', 'user_reference'):
                    user_id = assignee.get('id')
                    self._user_incident_counts[user_id] = \
                        self._user_incident_counts.get(user_id, 0) + 1

    def get_user_incident_count(self, user_id):
        """Get the number of open incidents for a specific user"""
        self.get_open_incidents()
        return self._user_incident_counts.get(user_id, 0)

    def get_users_with_open_incidents(self):
        """Get set of user IDs that have open incidents"""
        self.get_open_incidents()
        return set(self._user_incident_counts.keys())


class OrphanUsersFinder:
    """
    Finds users not associated with any schedules, escalation policies, or teams.
    Also tracks open incidents assigned to users.
    """

    def __init__(self, cache):
        self.cache = cache
        self.users_in_schedules = set()
        self.users_in_escalation_policies = set()
        self.users_in_teams = set()
        self.users_with_incidents = set()

    def extract_users_from_schedules(self):
        """Extract all user IDs from all schedules"""
        log.info("Extracting users from schedules...")
        schedules = self.cache.get_schedules()
        for schedule in schedules:
            details = schedule.get('details', {})
            for user in details.get('users', []):
                self.users_in_schedules.add(user.get('id'))
            for layer in details.get('schedule_layers', []):
                for user_entry in layer.get('users', []):
                    user = user_entry.get('user', {})
                    self.users_in_schedules.add(user.get('id'))
        log.info("Found %d users in schedules", len(self.users_in_schedules))

    def extract_users_from_escalation_policies(self):
        """Extract all user IDs from all escalation policies"""
        log.info("Extracting users from escalation policies...")
        policies = self.cache.get_escalation_policies()
        for policy in policies:
            for rule in policy.get('escalation_rules', []):
                for target in rule.get('targets', []):
                    if target.get('type') in ('user', 'user_reference'):
                        self.users_in_escalation_policies.add(target.get('id'))
        log.info("Found %d users in escalation policies", len(self.users_in_escalation_policies))

    def extract_users_from_teams(self):
        """Extract all user IDs from all teams"""
        log.info("Extracting users from teams...")
        teams = self.cache.get_teams()
        for team in teams:
            team_user_ids = self.cache.get_team_users(team['id'])
            self.users_in_teams.update(team_user_ids)
        log.info("Found %d users in teams", len(self.users_in_teams))

    def extract_users_with_open_incidents(self):
        """Extract all user IDs that have open incidents assigned"""
        log.info("Extracting users with open incidents...")
        self.users_with_incidents = self.cache.get_users_with_open_incidents()
        log.info("Found %d users with open incidents", len(self.users_with_incidents))

    def find_orphan_users(self):
        """Find users not in any schedule, escalation policy, or team"""
        self.extract_users_from_schedules()
        self.extract_users_from_escalation_policies()
        self.extract_users_from_teams()
        self.extract_users_with_open_incidents()

        all_users = self.cache.get_users()
        all_user_ids = {u['id'] for u in all_users}

        associated_users = (
            self.users_in_schedules |
            self.users_in_escalation_policies |
            self.users_in_teams
        )

        orphan_user_ids = all_user_ids - associated_users

        orphan_users = []
        for user in all_users:
            if user['id'] in orphan_user_ids:
                user_id = user['id']
                open_incident_count = self.cache.get_user_incident_count(user_id)
                orphan_users.append({
                    'id': user_id,
                    'name': user.get('name'),
                    'email': user.get('email'),
                    'role': user.get('role'),
                    'job_title': user.get('job_title', ''),
                    'time_zone': user.get('time_zone', ''),
                    'in_schedules': False,
                    'in_escalation_policies': False,
                    'in_teams': False,
                    'has_open_incidents': open_incident_count > 0,
                    'open_incident_count': open_incident_count
                })

        log.info("Found %d orphan users out of %d total users",
                 len(orphan_users), len(all_users))
        return orphan_users

    def find_partially_orphaned_users(self):
        """
        Find users with detailed association info.
        Returns all users with flags indicating their associations.
        """
        self.extract_users_from_schedules()
        self.extract_users_from_escalation_policies()
        self.extract_users_from_teams()
        self.extract_users_with_open_incidents()

        all_users = self.cache.get_users()
        user_report = []

        for user in all_users:
            uid = user['id']
            in_schedules = uid in self.users_in_schedules
            in_eps = uid in self.users_in_escalation_policies
            in_teams = uid in self.users_in_teams
            open_incident_count = self.cache.get_user_incident_count(uid)

            user_report.append({
                'id': uid,
                'name': user.get('name'),
                'email': user.get('email'),
                'role': user.get('role'),
                'job_title': user.get('job_title', ''),
                'time_zone': user.get('time_zone', ''),
                'in_schedules': in_schedules,
                'in_escalation_policies': in_eps,
                'in_teams': in_teams,
                'has_open_incidents': open_incident_count > 0,
                'open_incident_count': open_incident_count,
                'is_orphan': not (in_schedules or in_eps or in_teams)
            })

        return user_report


class ReportGenerator:
    """Generates reports in various formats"""

    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

    def generate_csv_report(self, users, filename=None):
        """Generate a CSV report of users"""
        if filename is None:
            filename = 'orphan_users_%s.csv' % datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.output_dir, filename)

        fieldnames = [
            'id', 'name', 'email', 'role', 'job_title', 'time_zone',
            'in_schedules', 'in_escalation_policies', 'in_teams',
            'has_open_incidents', 'open_incident_count', 'is_orphan'
        ]

        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                writer.writerow(user)

        log.info("CSV report saved to %s", filepath)
        print("CSV report saved to: %s" % filepath)
        return filepath

    def generate_json_report(self, users, filename=None):
        """Generate a JSON report of users"""
        if filename is None:
            filename = 'orphan_users_%s.json' % datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w') as jsonfile:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_users': len(users),
                'orphan_count': sum(1 for u in users if u.get('is_orphan', True)),
                'users': users
            }, jsonfile, indent=2)

        log.info("JSON report saved to %s", filepath)
        print("JSON report saved to: %s" % filepath)
        return filepath

    def print_summary(self, users):
        """Print a summary to console"""
        total = len(users)
        orphans = [u for u in users if u.get('is_orphan', True)]
        in_schedules = sum(1 for u in users if u.get('in_schedules'))
        in_eps = sum(1 for u in users if u.get('in_escalation_policies'))
        in_teams = sum(1 for u in users if u.get('in_teams'))
        with_incidents = sum(1 for u in users if u.get('has_open_incidents'))
        total_incidents = sum(u.get('open_incident_count', 0) for u in users)
        orphans_with_incidents = [u for u in orphans if u.get('has_open_incidents')]

        print("\n" + "=" * 60)
        print("PAGERDUTY USER ASSOCIATION REPORT")
        print("=" * 60)
        print("Total Users:                    %d" % total)
        print("Users in Schedules:             %d" % in_schedules)
        print("Users in Escalation Policies:   %d" % in_eps)
        print("Users in Teams:                 %d" % in_teams)
        print("-" * 60)
        print("Users with Open Incidents:      %d" % with_incidents)
        print("Total Open Incidents:           %d" % total_incidents)
        print("-" * 60)
        print("Orphan Users (no associations): %d" % len(orphans))
        print("Orphans with Open Incidents:    %d" % len(orphans_with_incidents))
        print("=" * 60)

        if orphans_with_incidents:
            print("\nORPHAN USERS WITH OPEN INCIDENTS (Action Required):")
            print("-" * 60)
            for user in orphans_with_incidents:
                print("  - %s <%s> [%s] - %d open incident(s)" % (
                    user['name'], user['email'], user['role'],
                    user['open_incident_count']))

        orphans_without_incidents = [u for u in orphans if not u.get('has_open_incidents')]
        if orphans_without_incidents:
            print("\nOrphan Users (no open incidents):")
            print("-" * 60)
            for user in orphans_without_incidents:
                print("  - %s <%s> [%s]" % (
                    user['name'], user['email'], user['role']))
        print("")


def setup_logging(verbose):
    """Initialize logging"""
    logdir = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    logfile = os.path.join(logdir, 'orphan_report_%s.log' %
                           datetime.now().strftime('%Y%m%d_%H%M%S'))

    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    fileh = logging.FileHandler(logfile)
    fileh.setFormatter(file_formatter)
    log.addHandler(fileh)
    log.setLevel(logging.INFO)

    if verbose:
        stderrh = logging.StreamHandler()
        stderrh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        log.addHandler(stderrh)
        log.setLevel(logging.DEBUG)


def main(args):
    setup_logging(args.verbose)
    log.info("Starting PagerDuty Orphan Users Report")

    cache = PagerDutyCache(args.access_token, args.from_email)
    finder = OrphanUsersFinder(cache)

    if args.full_report:
        users = finder.find_partially_orphaned_users()
    else:
        users = finder.find_orphan_users()
        for u in users:
            u['is_orphan'] = True

    report_gen = ReportGenerator(args.output_dir)
    report_gen.print_summary(users)

    if args.csv:
        report_gen.generate_csv_report(users)
    if args.json:
        report_gen.generate_json_report(users)

    log.info("Report generation complete")
    print("Script complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find PagerDuty users not associated with any resources')
    parser.add_argument(
        '--access-token', '-a',
        help="PagerDuty REST API access token",
        dest='access_token',
        required=True
    )
    parser.add_argument(
        '--from-email', '-f',
        help="Email address of the requesting user",
        dest='from_email',
        required=True
    )
    parser.add_argument(
        '--csv', '-c',
        help="Generate CSV report",
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--json', '-j',
        help="Generate JSON report",
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--full-report', '-r',
        help="Include all users with association flags, not just orphans",
        dest='full_report',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--output-dir', '-o',
        help="Output directory for reports (default: reports)",
        dest='output_dir',
        default='reports'
    )
    parser.add_argument(
        '--verbose', '-v',
        help="Verbose output",
        action='store_true',
        default=False
    )
    args = parser.parse_args()
    main(args)