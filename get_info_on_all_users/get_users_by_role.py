#!/usr/bin/env python

import argparse
import pdpyras
import sys
import csv

# create a dictionary to keep track of how many people are in each role
role_types_count = {}
allowed_roles=['admin','read_only_user','read_only_limited_user','user','limited_user','observer','restricted_access','owner']
team_managers=[]

def write_rows(column1, column2):
  with open(filename, 'a+') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([column1, column2])


def get_users(role, session):
  role_types_count[role] = 0
  if args.logging: 
    sys.stdout.write("Listing %ss:\n"%role)
  members = [] 
  for user in session.iter_all('users'): 
    if user['role'] == role:
      role_types_count[role] += 1
      if args.logging: 
        sys.stdout.write(user['name'] + "\n")
      write_rows(user['name'], role)
      members.append(user['name'])
  total_for_role = str(len(members))
  if args.logging:   
    sys.stdout.write("Total number of "+role+"s: "+total_for_role)
    sys.stdout.write("\n-----\n")


def get_managers(team_id, team_name, session):
  for member in session.iter_all('teams/%s/members'%team_id):
    if member['role'] == 'manager':
      role_types_count['team managers'] += 1
      if args.logging: 
        sys.stdout.write(member['user']['summary'] + "\n")
      write_rows([member['user']['summary'], "Team Manager, " + team_name])
      team_managers.append(member['user']['summary'])
    

def get_teams(session):
  role_types_count['team managers'] = 0 
  for team in session.iter_all('teams'):
    team_name = (team['summary'])
    get_managers(team['id'], team_name, session)
  total_team_managers = str(len(team_managers))
  if args.logging: 
    sys.stdout.write("Total number of team managers: "+total_team_managers+"\n")
    sys.stdout.write("\n-----\n")
    

if __name__ == '__main__':
  ap = argparse.ArgumentParser(description="Retrieves all users with the role(s) "
      "stated in the command line argument")
  ap.add_argument('-k', '--api-key', required=True, help="REST API key")
  ap.add_argument('-r', '--roles', required=True, help="roles to be fetched", dest='roles')
  ap.add_argument('-f', '--filename', required=True, help="filename for csv", dest='filename')
  ap.add_argument('-v', '--logging', default=False, dest='logging', help="verbose logging", action='store_true')
  args = ap.parse_args()
  session = pdpyras.APISession(args.api_key)
  roles = (args.roles).split(',')
  if args.filename[-4:] != '.csv':
    filename = args.filename + '.csv'
  else:
    filename = args.filename
  write_rows('Name','Role')  
  for role in roles:
    if role == "team_managers":
      get_teams(session)
    elif role in allowed_roles:  
      get_users(role, session)
    else:  
      sys.stdout.write("\n"+role+" is not an acceptable value. Please only use the following values with the -r flag:\n")
      for api_value in allowed_roles:
        sys.stdout.write(api_value+"\n")
      sys.stdout.write("\n")  
  for role_type, total in role_types_count.items():
    sys.stdout.write(role_type+": "+str(total)+"\n")

# to write the totals for each role type at the bottom of the csv  
  # with open('member_roles.csv', 'a+') as csvfile:
  #   writer = csv.writer(csvfile)
  #   writer.writerow([])
  #   writer.writerow(["Role Type", "Total"])
  #   for role_type, total in role_types_count.items():
  #     writer.writerow([role_type, total])      
      
# This script will take a comma separated list of roles as a command line argument and fetches all the users in an account that match one of 
# roles provided in the list. Roles will be fetched in the order that they are provided in the command line argument. Running with -v flag will 
# show which role is being retrieved and then list the members who match it. After retrieving all the members for a given role, a tally will be 
# shown for how many users have that role. 
# The script also creates a csv with names in the first column and users in the second. At the bottom of the CSV the totals for each role type
# are listed.  
# how to run:
# python get_users_by_role.py -k API-KEY-HERE -r COMMA-SEPARATED-ROLES-LIST
# acceptable values for roles: admin,read_only_user,read_only_limited_user,user,limited_user,observer,restricted_access,owner
