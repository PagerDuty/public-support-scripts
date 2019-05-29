#!/usr/bin/env python

# PagerDuty Support asset: rerole_users

import argparse
import csv
import pdpyras
import sys
from six.moves import input

session = None
users = {}
teams = {}
team_members = {} # Indexed by team ID, each value a dict indexed by user ID

def decide_new_roles(args, user, per_user_base_role, per_user_team_role,
        per_user_per_team_roles=None):
    """
    Logic that dictates how the new role should be set.

    Individually specified new roles, i.e. team/base roles given in the CSV,
    should always override roles specified by command line arguments.

    :param args: Command line arguments namespace
    :param user: Dictionary represenation of the user
    :param per_user_base_role: If the base role is specified on a per-user basis
        in the CSV, this will be the role to set. Otherwise, it will be None.
    :param per_user_team_role: Special team role to set per-user. Follows the same
        logic as ``per_base_role``.
    :param per_user_per_team_roles: List of roles to set for each team.
    :returns: The first element is the base role to set for the user, and the
        second is the team-level role. If the value of an element is None, it is
        ignored (no permissions update occurrs); otherwise, the permissions are
        replaced with the returned value.
    :rtype: tuple
    """
    # Base role:
    if per_user_base_role is not None:
        base_role = per_user_base_role
    else:
        base_role = args.new_base_role

    if per_user_team_role is not None:
        # Individually specified
        team_role = per_user_team_role
    elif args.adapt_roles:
        # Derive new team role from current base role being replaced. This
        # creates a world where everyone has the same level of access as they
        # previously had, but only on their own teams. Typical use case would be
        # a quick and dirty way to implement least privilege without cutting
        # users off from being able to do their work, i.e. by setting
        # --new-role restricted_access and --adapt-team-roles
        #
        # Why not set a default role in the optional keyword argument? If the
        # user was restricted_access, for example, then it's safe to assume that
        # they already have some advanced team-level permissions set up and so
        # we don't really want to modify team roles for them here. Moreover,
        # there is not really any equivalent team-level role; rather, denying
        # access to view a team would be accomplished with the team's visibility
        # setting and/or making the user's base role restricted_access and _not_
        # granting them any role on the team. So in this case we must default to
        # None as the team level.
        team_role = team_role_from_base_role(user['role'])
        # Now some more validation and special adjustments.
        #
        # In the following scenario, Users->Managers and we're demoting admins
        # so let's give them manager access to best approximate what they were
        # previously:
        if user['role'] == 'admin' and base_role != 'admin':
            team_role = 'manager'
        if team_role is not None:
            print("Derived new team role {0} based on old role {1}".format(
                team_role, user['role']))
    else:
        # Use the command line argument specified as the default
        team_role = args.new_team_role

    # Can't give admins per-team permissions! It's a fixed role!
    if base_role == 'admin' and team_role is not None:
        print("Team-level role(s) specified for user "+user['summary']+", but "\
            "the user will be granted the admin role. Ignoring; admin is not "\
            "a flexible role.")
        team_role = None
        # Don't set any
        per_team_roles = {}
    # Decide on per-team roles:

    # High granualrity team roles:
    per_team_roles = per_user_per_team_roles
    decided_per_team_roles = {}
    if per_user_per_team_roles is None:
        per_team_roles = {}
    for (t, r) in per_team_roles.items():
        if not t or not t.strip():
            # Blank team column
            continue
        per_team_role = r
        if r is None:
            # Default to the globally-set team role, determined by the logic
            # in the above code:
            per_team_role = team_role
        decided_per_team_roles[t] = valid_role(per_team_role, team=True)

    return [valid_role(base_role), valid_role(team_role, team=True),
        decided_per_team_roles]

def configure_new_roles(args, user, base_role, team_role, per_team_roles=None):
    """
    Set new roles for a given user

    :arg args: command line arguments namespace object
    :arg user: User as a dictionary object
    :arg per_user_base_role: Base role specified on an individual basis
    :arg per_user_team_role: Team role specified on an individual basis
    """
    user_id = user['id']
    prev_base_role = user['role']
    prev_team_role = None
    prev_team_roles = []
    # Set roles
    print("Setting roles for user: \"%s\" <%s> (ID=%s)"%(
        user['summary'], user['email'], user_id))
    if base_role is not None:
        set_base_role(user_id, base_role, prev_base_role)
    if team_role is not None and not per_team_roles:
        prev_team_roles = list(set_role_on_all_teams(user_id, team_role,
            user['teams']))
    if per_team_roles is not None and len(per_team_roles):
        for (team_name, role) in per_team_roles.items():
            team = find_team(team_name)
            if not team:
                print("WARNING: team not found: \"%s\"; skipping."%name)
                continue
            prev_role = set_user_role_on_team(user_id, role, team['id'])
            prev_team_roles.append((role, team['name']))
    return [user['email'], prev_base_role, prev_team_roles]

def find_team(name):
    """
    Looks up and memoizes a user based on their name.

    :param name: Name of the team. Must be a verbatim match.
    """
    global session, teams
    try:
        team = teams.get(name, None)
        if team is None:
            team = session.find('teams', name)
            if team is None:
                print("WARNING: team not found: "+name)
                teams[name] = False
            else:
                teams[name] = team
        return teams[name]
    except pdpyras.PDClientError as e:
        handle_exception(e)

def find_user(email):
    """
    Looks up and memoizes a user based on their email address.

    :param email: User email address.
    """
    global session, users
    try:
        # Try lookup by email first
        u_params = {'include[]':['teams']}
        user = users.get(email, None)
        if user is not None:
            return user
        user = session.find('users', email, attribute='email', params=u_params)
        if user is None:
            print("WARNING: user not found: "+email)
            users[email] = False
        else:
            users[email] = user
        return users[email]
    except pdpyras.PDClientError as e:
        handle_exception(e)

def get_team(team_id):
    global session, teams
    if team_id not in teams:
        teams[team_id] = session.rget('/teams/'+team_id)
    return teams[team_id]

def get_all_rerole_operations(args):
    """
    Put together a list of users and roles to set.

    :return:
        A list containing in each entry a  length-4 lists, each containing the
        user model dict, the base role to set, the team role to set on all teams
        and the per-user-per-team roles (if any) to set.
    :rtype: list
    """
    # Created this variable just so we can check if each user is a stakeholder,
    # but only give a warning for the first one
    stakeholder_permission= 0

    # Apply logic to determine what base/team roles to grant via
    # decide_new_roles on each item returned by get_users
    for rerole_task in get_users(args):
        user, base_role, team_role, per_team_roles = rerole_task
        if user['role'] in args.skip_roles:
            print("User %s has role we're intentionally skipping: %s"%(
                user['name'], user['role']))
            continue
        if user['role'] == 'read_only_user' and stakeholder_permission ==0:
            confirm_stakeholder_change = input('''
                The users whose roles you are attempting to change have
                stakeholder licenses. If this change has been requested or
                approved by the billing department, proceed by entering \'y\'.
                Otherwise, please abort by entering \'n\' and reach out to the
                CSM.\n\n\n''')

            if confirm_stakeholder_change == "n":
                exit(0)

            elif confirm_stakeholder_change == "y":
                stakeholder_permission += 1

        rerole_spec = decide_new_roles(args, user, base_role, team_role,
            per_team_roles)
        yield [user, rerole_spec]

def get_rerole_stats(rerole_ops):
    """
    Gets a summary of information about the rerole operation.
    """
    stats = {'base': {}, 'team':{}}
    users = {'base': {}, 'team':{}}
    for (user, role_spec) in rerole_ops:
        to = role_spec[:2]
        per_team = role_spec[2]
        if len(per_team):
            # Not yet supported; sorry!
            return None
        for (i, roletype) in enumerate(('base', 'team')):
            if to[i] is not None:
                if user['email'] in users[roletype]:
                    print("WARNING: %s role for %s already defined as %s"%(
                        roletype, user['email'], users[roletype][user['email']]
                    ))
                    continue
                stats[roletype][to[i]] = stats[roletype].get(to[i], 0)+1
                users[roletype][user['email']] = to[i]
    return stats

def get_team_members(team_id):
    """
    Retrieve and memoize roles of members of a team.

    :param team_id: ID of the team to retrieve.
    :returns: A dictionary object mapping user IDs to the role that they have on
        the team given by the team ID.
    """
    global session, team_members
    if team_id not in team_members:
        r = session.get('teams/%s/members'%team_id)
        if r.ok:
            team_members.setdefault(team_id, {})
            for member in r.json()['members']:
                if not 'user' in member:
                    # Ignore if not a user
                    continue
                team_members[team_id][member['user']['id']] = member['role']
        else:
            print("WARNING: couldn't retrieve members of team %s"%team_id)
            team_members[team_id] = {}
    return team_members[team_id]

def get_user_role_on_team(team_id, user_id):
    """Gets the current role of a user on a team."""
    global session
    members = get_team_members(team_id)
    if user_id in members:
       return members[user_id]

def get_user(email_or_name):
    global session

def get_users(args):
    """
    Generator for iterating over users.

    If the --users-from-file or --roles-from-file option was not specified, this
    will include all users.

    :arg args: Command line arguments namespace
    :yields: A list: the first element is the user as a dictionary object, the
        second is a per-user base role to set (or None to default to the role
        given in the command line options), the third is a team-level role to 
        set for the given user, or none to default to the team role given in the
        command line options, and the fourth is a dict of per-user-per-team
        permissions (or an empty array, if none were specified), each item of
        which is a dict mapping teams of the user to roles that the user
        should acquire on each team.
    :rtype: tuple
    """
    global session, users
    if args.all_users:
        print("Getting ALL users (all of them will be re-roled)...")
        try:
            for user in session.iter_all('users'):
                users[user['email']] = user
                yield [user, None, None, {}]
        except Exception as e:
            handle_exception(e)
    elif args.teamroles_file is None:
        # Bring in users and roles listed in the CSV
        print("Getting users to re-role as specified in the file...")
        roles_file = csv.reader(args.roles_file)
        for (i, item) in enumerate(roles_file):
            # Roles from CSV: Treat empty entries as meaning "do not set
            # this role and defer to the command line options"; otherwise,
            # use the roles as given in the file:
            # user_email, base_role, team_role
            #
            # Notes: 
            # - Format can safely be rather loose; there can be anywhere from
            #   one to three columns whitespace will be stripped out and
            #   ignored.
            # - If only one column is present, that should be user emails.
            # - If there are two columns, the first is user email and the second
            #   is a base role to set.
            # - If there are three columns, the first row is the emails, the
            #   second is the base role and the third is a team role to set on
            #   all the user's teams
            role = None
            team_role = None
            user_email = item[0].strip()
            if len(item) > 1 and len(item[1].strip()):
                # Non-empty base role present
                role = item[1].strip()
            if len(item) > 2 and len(item[2].strip()):
                # Non-empty team role present
                team_role = item[2].strip()
            if not user_email:
                print("Empty name/email given; skipping row %d of input"%(i+1))
                continue
            # Look up user
            user = find_user(user_email.strip())
            if not user:
                print("Could not find user by name or email: " + user_email)
                continue
            yield [user, role, team_role, {}]
    else: # Per-user-per-team roles
        print("Getting per-team roles for users as specified in the file...")
        team_roles = {}
        roles_file = csv.reader(args.teamroles_file)
        for row in roles_file:
            email, team_role, team_name = [c.strip() for c in row]
            user = find_user(email)
            team = find_team(team_name)
            if user and team:
                team_role = valid_role(team_role, team=True)
                if not team_role:
                    continue
                print("%s: %s on %s"%(email, team_role, team['summary']))
                team_roles.setdefault(email, {})
                team_roles[email][team_name] = team_role
        for email in team_roles:
            yield [users[email], None, None, team_roles[email]]

def handle_exception(e):
    msg = "API Error: %s ; "%e
    response = e.response
    if response is not None:
        msg += "HTTP %d for %s %s: %s"%(response.status_code,
            response.request.method, response.url, response.text)
    print(msg)
    return response

def print_rerole_stats(rerole_stats):
    for roletype in rerole_stats:
        print("Users whose %s role will be set:"%roletype)
        for role in rerole_stats[roletype]:
            print("\tTo %s: %d"%(role, rerole_stats[roletype][role]))

def rerole_users(args):
    # Set up rollback file, if specified
    rf = None
    trf = None
    if args.rollback_file is not None:
        rf = csv.writer(args.rollback_file)
    if args.rollback_teamroles_file is not None:
        trf = csv.writer(args.rollback_teamroles_file)

    # Prepare, present user with summary and prompt for Y/N to proceed
    print("Collecting list of user rerole operations...")
    rerole_ops = list(get_all_rerole_operations(args))
    n_tot = len(set([o[0]['email'] for o in rerole_ops]))
    rerole_stats = get_rerole_stats(rerole_ops)
    if rerole_stats is not None:
        print_rerole_stats(rerole_stats)

    # Check for backup file option
    if not args.assume_yes and (rf is None or trf is None):
        cont = input("No rollback file specified for base and/or team roles.\n"
            "\nIt is highly recommended that you specify both backup options, "
            "to store the existing role data (as a backup) via options -m/-b "
            "(see the helptext by running with -h/--help for more details).\n\n"
            "Without these options, you'll be SOL in the event that something "
            "goes wrong and you need to revert changes.\n\n"
            "That being said, are you ABSOLUTELY SURE you want to proceed? "
            "(y/n) ")
        cont = cont.strip().lower()[0] == 'y'
        if not cont:
            print("Aborted.")
            return

    # Proceed
    for (user, role_spec) in rerole_ops:
        (base_role, team_role, team_roles) = role_spec
        prev_role_spec = configure_new_roles(args, user, base_role, team_role,
            per_team_roles=team_roles)
        if rf is not None:
            # Just set base role in this file; it's not feasible to record all
            # the team roles in this file
            # email, base_role
            rf.writerow(prev_role_spec[:2])
        if trf is not None:
            email = prev_role_spec[0]
            for (role, team) in prev_role_spec[2]:
                trf.writerow([email, role, team])

def set_base_role(user_id, new_base_role, prev_base_role):
    global session
    try:
        print("Setting base role for user %s: %s (was %s)"%(user_id,
            new_base_role, prev_base_role))
        r = session.put('users/'+user_id, json={"user":{"role": new_base_role}})
        if r.ok:
            print("Success")
        else:
            print("Failed to set role for user: "+user_id)
    except pdpyras.PDClientError as e:
        handle_exception(e)

def set_role_on_all_teams(user_id, new_team_role, teams):
    """
    Sets the role of a user on a list of teams 

    :param user_id: The PagerDuty ID of the user
    :param new_team_role: 
    :param teams: A list of teams on which to operate
    :yields: A 2-tuple of the previous role on the team and the team name, or
        None if they were not already a member.
    """
    global session
    for team in teams:
        print("Setting role for user %s on team %s (%s) to %s"%(
            user_id, team['summary'], team['id'], new_team_role))
        yield (set_user_role_on_team(user_id, new_team_role, team['id']),
            team['summary'])

def set_user_role_on_team(user_id, new_team_role, team_id, add_to_teams=False):
    """
    Sets a new role for a user on a team of which they are already a member.

    This function itself supports adding the user to the team if not already a
    member, but the script as a whole can't utilize this yet. We'd have to pass
    the command line arguments through another few layers of the stack...

    :param user_id: The PagerDuty ID of the user
    :param new_team_role: 
    :param team_id: ID of the team on which the role should be set.
    :param add_to_teams: If True, the user should be added to the team;
        otherwise, if the user is not already a member, skip them.
    :returns: The previous role on the team, or None if they were not already a
        member
    :rtype: str or None
    :param user_id: 
    """
    prev_role = get_user_role_on_team(team_id, user_id)
    params = {"role": new_team_role}
    if prev_role is None:
        if not add_to_teams:
            print("WARNING: user %s is not on team %s, so they are NOT going "
                "to be added, and no role will be set for them on this team."%(
                    user_id, team_id))
            return prev_role
        else:
            print("WARNING: user %s is not on team %s, so they are going to "
                "be added. If you want to roll back changes, you will have to "
                "remove them from this team manually."%(user_id, team_id))
    print("Setting role of user %s on team %s to %s (was %s)"%(user_id, team_id,
        new_team_role, prev_role))
    request = session.put('teams/%s/users/%s'%(team_id, user_id), json=params)
    if request.ok:
        print("Success")
    else:
        print("API error (%d): %s"%(request.status_code, request.text))
    return prev_role

def team_role_from_base_role(base_role, default=None):
    """
    Converts a ``user.role`` value to equivalent team role value

    :param base_role: The role value that would typically be user's base role
    :param default: The default value if no equivalent is found.
    """
    team_role = default
    if base_role in ('team_responder', 'limited_user'):
        # In both these cases, their permissions should be to respond to
        # incidents on their team.
        team_role = 'responder'
    elif base_role == 'user':
        team_role = 'manager'
    elif base_role == 'observer':
        team_role = 'observer'
    elif base_role == 'admin':
        team_role = None
    return team_role

def valid_role(role, team=False):
    """
    Validates a role, returning it if it's valid or None if it's invalid.

    :param role: The role to validate
    :param team: True if this is a team role we are validating
    :rtype: None, str
    """
    roletype = ('base', 'team')[int(team)]
    valid_roles = {
        'base': ['restricted_access', 'observer', 'limited_user', 'user',
            'admin'],
        'team': ['observer', 'manager', 'responder']
    }[roletype]
    if role in valid_roles or role is None:
        return role
    else:
        msg = "WARNING: Ignoring invalid {rt} role \"{role}\"; {rt} roles "\
            "must be one of the following: {roles}"
        print(msg.format(rt=roletype, role=role, roles=', '.join(valid_roles)))

def main():
    global session
    parser = argparse.ArgumentParser(description="Give users new roles. In "\
        "cases where the users' new roles are given on a per-user basis, i.e. "\
        "in a CSV, that will take precedence over roles specified via command "\
        "line arguments; both can be used. Note, this script cannot yet be "\
        "used to specify team roles on a per-team basis.")

    # General options
    helptxt = "PagerDuty full-access REST API key"
    parser.add_argument('-k', '--api-key', required=True, help=helptxt)
    parser.add_argument('-r', '--new-role', help="The users' new role.",
        dest='new_base_role', default=None)
    helptxt = "Roles such that, if a user has that role, they will be skipped "\
        "in the re-roling. To specify multiple roles, include this option "\
        "several times. This will always include the account owner (who "\
        "cannot be demoted through the API) and stakeholders (because "\
        "changing the stakeholder count can affect billing)."
    parser.add_argument('--skip-users-with-role', '-s', dest="skip_roles",
        action='append', default=['owner'], help=helptxt)

    # Team role setting options
    teamrole_args = parser.add_mutually_exclusive_group()
    helptxt = "New team-level role to set for users on their respective teams."
    teamrole_args.add_argument('-e', '--team-role', dest='new_team_role',
        required=False, default=None, help=helptxt)
    helptxt = "Derive the users' new team roles from their current default "\
            "roles, which will be replaced with the role specified by the "\
            "--new-role option. For instance, if a given user is a manager "\
            "and --new-role is observer, they will have manager access to "\
            "their teams but a new base role of observer."
    teamrole_args.add_argument('-u', '--auto-team-roles', dest='adapt_roles',
        required=False, default=False, action='store_true', help=helptxt)

    # Input file options
    from_file = parser.add_mutually_exclusive_group(required=True)
    helptxt = "Rerole all users in the account."
    from_file.add_argument('-a', '--all-users', dest='all_users', default=False,
        action='store_true', help=helptxt)
    helptxt = "File specifying list of user roles. The file should be a CSV "\
        "with user login email as the first column and role as the second, "\
        "and optionally the third column the team role to give them."
    from_file.add_argument('-o', '--roles-from-file', dest='roles_file',
        default=None, type=argparse.FileType('r'), help=helptxt)
    helptxt="File specifying list of users, one login email per line."
    helptxt="File specifying per-user per-team roles to set. The file should "\
        "be a CSV with the user login email as the first colum, the team "\
        "role as the second column, and the name of the team on which the "\
        "user has that role as the third. Note, you can include an individual "\
        "user multiple times in the same file to set distinct roles on any "\
        "number of teams."
    from_file.add_argument('-t', '--team-roles-from-file',
        dest='teamroles_file', type=argparse.FileType('r'), default=None,
        help=helptxt)

    # Output (save) file option:
    helptxt = "File to which the prior user base roles should be written. "\
        "Files written to with this option can then be used to reset the "\
        "permissions to the previous state before having run the rerole "\
        "script, via the --roles-from-file option."
    parser.add_argument('-b', '--rollback-file', dest='rollback_file',
        default=None, type=argparse.FileType('w'), help=helptxt)
    helptxt = "File to which the prior user team roles should be written. "\
        "Files written to with this option can then be used to reset the "\
        "fine-grained per-user-per-team roles to the previous state before "\
        "having run the rerole script, via the --team-roles-from-file option."
    parser.add_argument('-m', '--rollback-teamroles-file', 
        dest='rollback_teamroles_file', type=argparse.FileType('w'),
        help=helptxt)
    helptxt="Assume a yes answer to all prompts i.e. to proceed in the case "\
        "that no backup file was specified."
    parser.add_argument('-y', '--yes-to-all', default=False, dest='assume_yes',
        action='store_true', help=helptxt)

    args = parser.parse_args()

    # Print a conspicuous warning message to avoid making a big mistake
    if args.all_users and not args.assume_yes:
        cont = False
        cont = input("THIS WILL UPDATE ALL USERS IN THE ACCOUNT. Are you sure "
            "you want to proceed? ")
        cont = cont.strip().lower() == 'y'
        if not cont:
            print("Aborted.")
            return

    session = pdpyras.APISession(args.api_key)
    rerole_users(args)

if __name__=='__main__':
    main()
