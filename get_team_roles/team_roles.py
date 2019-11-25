import argparse
import sys
import pdpyras

def get_teams(session, comma_separated):
    if comma_separated:
        sys.stdout.write("Team ID, Team Name, User ID, User name, Team role\n")
    for team in session.iter_all('teams'):
        get_team_members(team['id'], team['name'], session, comma_separated)

def get_team_members(team_id, team_name, session, comma_separated):
    for member in session.iter_all('teams/{}/members'.format(team_id)):
        if comma_separated:
            sys.stdout.write("{}, {}, {}, {}, {}\n".format(team_id, team_name, member['user']['id'], member['user']['summary'], member['role']))
        else:
            sys.stdout.write("Team ID: {}\n".format(team_id))
            sys.stdout.write("Team Name: {}\n".format(team_name))
            sys.stdout.write("User ID: {}\n".format(member['user']['id']))
            sys.stdout.write("User name: {}\n".format(member['user']['summary']))
            sys.stdout.write("Team role: {}\n".format(member['role']))
            sys.stdout.write("-----\n")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves team roles for"
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-c', '--comma-separated', required=False, default=False, action='store_true', help="Format output separated by commas")
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    get_teams(session, args.comma_separated)