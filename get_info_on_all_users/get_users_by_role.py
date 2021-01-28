#!/usr/bin/env python

import argparse
import pdpyras
import sys
import csv

 

team_managers=[]

def get_users(role, session):
    sys.stdout.write("Listing %ss:\n"%role)
    members = [] 
    with open('member_roles.csv', 'a+') as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(['Name', 'Role'])
      for user in session.iter_all('users'): 
        if user['role'] == role:
          sys.stdout.write(user['name'] + "\n")
          writer.writerow([user['name'], role])
          members.append(user['name'])
      total_for_role = str(len(members))   
      sys.stdout.write("Total number of "+role+"s: "+total_for_role)
      sys.stdout.write("\n-----\n")

def get_managers(team_id, team_name, session):
    with open('member_roles.csv', 'a+', newline='') as csvfile:
      writer = csv.writer(csvfile) 
      for member in session.iter_all('teams/%s/members'%team_id):
        if member['role'] == 'manager':
          sys.stdout.write(member['user']['summary'] + "\n")
          writer.writerow([member['user']['summary'], "Team Manager, " + team_name])
          team_managers.append(member['user']['summary'])
    

def get_teams(session):
    for team in session.iter_all('teams'):
      team_name = (team['summary'])
      get_managers(team['id'], team_name, session)
    total_team_managers = str(len(team_managers))
    sys.stdout.write("Total number of team managers: "+total_team_managers+"\n")
    

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves all users with the role(s) "
        "stated in the command line argument")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-r', '--roles', required=True, help="roles to be fetched", dest='roles')
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    roles = (args.roles).split(',')
    for role in roles:
      if role == "team_managers":
        get_teams(session)
      else:  
        get_users(role, session)
      



# acceptable values for roles: admin,read_only_user,read_only_limited_user,user,limited_user,observer,restricted_access,owner
