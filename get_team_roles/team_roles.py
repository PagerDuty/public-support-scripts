#!/usr/bin/env python
#
# Copyright (c) 2020, PagerDuty, Inc. <info@pagerduty.com>
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

# PagerDuty Support asset: get_team_roles

import argparse
import sys
import csv
from pdpyras import APISession, PDClientError

def get_teams(session, args):
    if args.comma_separated:
        print("'Team ID', 'Team Name', 'User ID', 'User name', 'Email', 'Base role', 'Team role'\n")
    elif args.csv_file:
        tf = csv.writer(args.csv_file)
        print("Creating / Clearing : {}\n".format(args.csv_file.name))
        tf.writerow(['Team ID', 'Team Name', 'User ID', 'User name', 'Email', "Base role", 'Team role'])
    try:
        for team in session.iter_all('teams'):
            get_team_members(team['id'], team['name'], session)
    except PDClientError as e:
        raise e

def get_team_members(team_id, team_name, session):
    users = {}
    try:
        for member in session.iter_all('teams/{}/members'.format(team_id), paginate=True):
            add_to_cache_users(member['user']['id'], users, session)
            user = users[member['user']['id']]
            if args.comma_separated:
                print("{}\n".format(",".join([team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']])))
            elif args.csv_file:
                tf = csv.writer(args.csv_file)
                tf.writerow([team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']])
                print("Added to {}: {}\n".format(args.csv_file.name, ",".join([team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']])))

            else:
                print("Team ID: {}\n".format(team_id))
                print("Team Name: {}\n".format(team_name))
                print("User ID: {}\n".format(user['id']))
                print("User name: {}\n".format(user['name']))
                print("User email: {}\n".format(user['email']))
                print("Base role: {}\n".format(user['role']))
                print("Team role: {}\n".format(member['role']))
                print("-----\n")
    except PDClientError as e:
        print("Could not get team members for team {} {}".format(team_name, team_id))
        raise e

def add_to_cache_users(user_id, users, session):
    if user_id in users:
        return 
    else: 
        try:
            user = session.rget('users/{}'.format(user_id))
            users[user_id] = user
            return 
        except PDClientError as e:
            print("Could not get user date for {}".format(user_id))
            raise e

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves team roles for"
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-c', '--comma-separated', required=False, default=False, action='store_true', help="Format output separated by commas")
    ap.add_argument('-f', '--csv-file', required=False, default=False, type=argparse.FileType('w'), help="Output to a csv file")
    args = ap.parse_args()
    session = APISession(args.api_key)
    get_teams(session, args)
