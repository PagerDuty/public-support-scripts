#!/usr/bin/env python

"""import_permissions.py

See README for further information; use -h flag to see command line usage.
"""

import argparse
import csv
import json
import logging
import requests
import sys

from pdreq import APIConnection

API = None

valid_roles = {
    # Team context
    'flexible': ["manager", "responder", "observer"], 
    # Global context
    'fixed': ["admin", "account_owner", "read_only_user"]
}

valid_object_types = {
    'escalation_policy': 'escalation_policies',
    'schedule': 'schedules',
    'service': 'services',
    'team': 'teams'
}

def logging_init(verbosity,logfile=None):
    global STDOUT
    level = ('ERROR', 'WARN', 'INFO', 'DEBUG')
    logformat = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s'
    )
    # We're just going to use the root logger because it's a standalone script
    # No need to organize everything by module
    logger = logging.getLogger()
    logger.setLevel(getattr(logging,level[verbosity]))
    cmdout = logging.StreamHandler(stream=sys.stdout)
    cmdout.setFormatter(logformat)
    logger.addHandler(cmdout)
    if logfile is not None:
        fh = logging.StreamHandler(stream=logfile)
        fh.setFormatter(logformat)
        logger.addHandler(fh)

def logrow(message,row,*fmtargs):
    """Prints information about a row in the CSV that couldn't be processed."""
    logging.warn(message, *fmtargs)
    logging.debug("Row: "+",".join(row))

def parse_args():
    """Parse command line arguments.

    Command line arguments are defined and parsed here.
    """
    parser = argparse.ArgumentParser(
        description="Import custom permissions from a CSV."
    )
    parser.add_argument('api_key',type=str,
        help="""A full access (read/write) v2 API key.""")
    parser.add_argument('csv_file',type=argparse.FileType('r'), help="""Path to
        the CSV file to be parsed.""")
    parser.add_argument('-l', '--log-file', dest='logfile', required=False,
        default=None, type=argparse.FileType('w'), help="""Optional log file to 
        save output messages.""")
    parser.add_argument('-v', '--verbose', dest='verbosity', action='count',
        default=0, help="""Logging verbosity level; maximum level 3 (-vvv).""")
    return parser.parse_args()

def parse_permissions(csviter):
    """Parses permissions out of a CSV file.

    The returned object is a dictionary mapping user IDs to the roles object.
    """
    global API
    users = {} # email : user
    roles = {} # email : role : objects
    objects = {} # type-name : object
    permissions = {} # email : role : objects
    skip = 0
    importing = 0
    for row in csviter:
        email, role, object_type, object_name = row
        if role not in valid_roles['flexible']:
            logrow("Skipping row because of invalid role: \"%s\"", row, role)
            skip += 1
            continue
        if email in users:
            user = users[email]
        else:
            try:
                user = API.get_object('users', email, matchattr='email')
                if not user:
                    logging.warn("No user found with email address %s", email)
            except Exception as e:
                logrow("Could not process record due to API error: %s", row, 
                    str(e))
                skip += 1
                continue
            users[email] = user
            if user:
                logging.debug("Found user, id=%s, for email=%s", user['id'], 
                    email)

        if not user:
            logrow("Skipping user with email=%s due to the above issues.", row,
                 email)
            skip += 1
            continue

        # Validate user role
        if user['role'] in valid_roles['fixed']:
            logrow(("User for email %s has fixed global role %s; cannot "+
                "assign flexible permissions."), row, email, user['role'])
            users[email] = False
            skip += 1
            continue
        elif user['role'] not in valid_roles['flexible']:
            logrow("User for email %s has invald role \"%s\"", row, email,
                user['role'])
            user[email] = False
            skip += 1
            continue

        # Validate object type
        if object_type not in valid_object_types:
            logrow("Invalid object type: %s", row, object_type)
            skip += 1
            continue

        # Get object
        obj_ind = (object_type,object_name)
        plural_type = valid_object_types[object_type]
        if not obj_ind in objects:
            try:
                obj = API.get_object(plural_type, object_name)
                objects[obj_ind] = obj
                if obj:
                    logging.debug("Found object, type=%s matching name=%s: %s", 
                        object_type, object_name, obj['id'])
            except Exception as e:
                obj = False
                objects[obj_ind] = False
                logging.error(e)
        else:
            obj = objects[obj_ind]
        if not obj:
            logrow(("Object of type \"%s\", name \"%s\" not found or API "+
                "error; skipping."), row, object_type, object_name)
            skip += 1
            continue

        # Populate the list of permissions:
        if email not in permissions:
            permissions[email] = {}
        if role not in permissions[email]:
            permissions[email][role] = set([])
        permissions[email][role].add(obj_ind)
        importing += 1

    logging.info("Total rows processed: %d; skipped: %d",importing+skip,skip)
    # Compose the permissions payload list:
    all_permissions = {}
    for email in permissions:
        user_id = users[email]['id']
        all_permissions[user_id] = {'roles': []}
        for (role,obj_inds) in permissions[email].items():
            all_permissions[user_id]['roles'].append({
                'resources': [{
                        'id':objects[oi]['id'], 
                        'type': oi[0]+'_reference'
                    } for oi in obj_inds],
                'role': role,
                'type': 'role',
                'user_id': user_id
            })
    return all_permissions

def set_permissions(user_id, roles):
    """Saves permissions for a user."""
    global API
    logging.debug("Setting permissions for user_id=%s...",user_id)
    resp = API.post(
        '/users/%s/roles'%user_id,
        payload=roles
    )
    if resp.status_code // 100 == 2:
        logging.debug("Successfully set permissions for user_id=%s")
    else:
        logging.error(("Could not set permissions for user_id=%s; API "+
            "responded with status code %d"), user_id, resp.status_code)

def main():
    global API

    args = parse_args()

    API = APIConnection(args.api_key)

    logging_init(args.verbosity, args.logfile)

    permissions = parse_permissions(csv.reader(args.csv_file))

    n_users = len(permissions)
    for (i,(user_id,roles)) in enumerate(permissions.items()):
        logging.info("Setting permissions for user %d/%d", i+1, n_users)
        set_permissions(user_id, roles)
    logging.info("Import complete; total API calls: %d", len(API._requests))

if __name__ == '__main__':
    main()
