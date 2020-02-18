import argparse
import sys
import pdpyras
import csv

def get_teams(session):
    if args.comma_separated:
        sys.stdout.write("Team ID', 'Team Name', 'User ID', 'User name', 'Email', 'Base role', 'Team role'\n")
    elif args.csv_file:
        tf = csv.writer(args.csv_file)
        sys.stdout.write("Creating / Clearing : {}\n".format(args.csv_file.name))
        tf.writerow(['Team ID', 'Team Name', 'User ID', 'User name', 'Email', "Base role", 'Team role'])
    try:
        for team in session.iter_all('teams'):
            get_team_members(team['id'], team['name'], session)
    except pdpyras.PDClientError as e:
        raise e

def get_team_members(team_id, team_name, session):
    try:
        for member in session.iter_all('teams/{}/members'.format(team_id), paginate=True):
            user = get_user_data(member['user']['id'], session)
            if args.comma_separated:
                sys.stdout.write("{}, {}, {}, {}, {}\n".format(team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']))
            elif args.csv_file:
                tf = csv.writer(args.csv_file)
                tf.writerow([team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']])
                sys.stdout.write("Added to {}: {}, {}, {}, {}, {}\n".format(args.csv_file.name, team_id, team_name, user['id'], user['name'], user['email'], user['role'], member['role']))

            else:
                sys.stdout.write("Team ID: {}\n".format(team_id))
                sys.stdout.write("Team Name: {}\n".format(team_name))
                sys.stdout.write("User ID: {}\n".format(user['id']))
                sys.stdout.write("User name: {}\n".format(user['name']))
                sys.stdout.write("User email: {}\n".format(user['email']))
                sys.stdout.write("Base role: {}\n".format(user['role']))
                sys.stdout.write("Team role: {}\n".format(member['role']))
                sys.stdout.write("-----\n")
    except pdpyras.PDClientError as e:
        print("Could not get team members for team {} {}".format(team_name, team_id))
        raise e

def get_user_data(user_id, session):
    if user_id in Users:
        return Users[user_id]
    else: 
        try:
            user = session.rget('users/{}'.format(user_id))
            Users[user_id] = user
            return Users[user_id]
        except pdpyras.PDClientError as e:
            print("Could not get user date for {}".format(user_id))
            raise e

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves team roles for"
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-c', '--comma-separated', required=False, default=False, action='store_true', help="Format output separated by commas")
    ap.add_argument('-f', '--csv-file', required=False, default=False, type=argparse.FileType('w'), help="Output to a csv file")
    Users = {}
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    get_teams(session)