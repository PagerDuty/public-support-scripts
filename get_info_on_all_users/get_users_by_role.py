#!/usr/bin/env python

import argparse
import pdpyras
import sys

users = []

def get_users(role, session):
    sys.stdout.write("Listing owner, global admins, and team managers:\n")
    for user in session.iter_all('users'):
      if user['role'] == role:
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
    ap = argparse.ArgumentParser(description="Retrieves all users with the role(s) "
        "stated in the command line argument")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-t', '--team-managers', required=False, default=False, action='store_true', help="fetch team managers")
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    roles = sys.argv[2:]
    for role in roles:
      get_users(role, session)

    if args.team_managers:   
      get_managers(session)
      get_teams(session)
      
    print_users()

