#!/usr/bin/env python

import argparse
import pdpyras
import sys

# Get all users' contact methods.
# Originally by Ryan Hoskin:
# https://github.com/ryanhoskin/pagerduty_get_all_contact_methods

users = []

def get_users(session):
    sys.stdout.write("Listing owner, global admins, and team managers:\n")
    for user in session.iter_all('users'):
      if user['role'] == 'admin' or user['role'] == 'owner':
    #   sys.stdout.write("User: ")
       users.append(user['name'])
    #   sys.stdout.write("\n")

def get_managers(team_id, session):
    for member in session.iter_all('teams/%s/members'%team_id):
     if member['role'] == 'manager':
    #   sys.stdout.write("User: ")
       users.append(member['user']['summary'])
    #   sys.stdout.write("\n")

def get_teams(session):
    for team in session.iter_all('teams'):
      get_managers(team['id'], session)
  
      #    sys.stdout.write("-----\n")

def print_users():
  set(users)
  for user in users:
    sys.stdout.write(user)
    sys.stdout.write("\n")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves contact info for all "
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    get_users(session)
    get_teams(session)
    print_users()

