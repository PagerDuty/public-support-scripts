#!/usr/bin/env python

import argparse
import pdpyras
import sys

# Disables noisy warning logging from pdpyras
import logging
logging.disable(logging.WARNING)

# Get all users' contact methods.
# Originally by Ryan Hoskin:
# https://github.com/ryanhoskin/pagerduty_get_all_contact_methods

def get_users(session):
    sys.stdout.write("Listing All Users' Contact Methods:\n")
    for user in session.iter_all('users'):
        sys.stdout.write("User: ")
        sys.stdout.write(user['name'])
        sys.stdout.write("\n")
        get_contact_methods(user['id'], session)
        sys.stdout.write("-----\n")

def get_contact_methods(user_id, session):
    for contact_method in session.iter_all('users/%s/contact_methods'%user_id):
        if 'phone' in contact_method['type']:
            sys.stdout.write("Phone:  ")
            sys.stdout.write('%s %s'%(contact_method['country_code'],
                contact_method['address']))
        elif 'sms' in contact_method['type']:
            sys.stdout.write("SMS:  ")
            sys.stdout.write('%s %s'%(contact_method['country_code'],
                contact_method['address']))
        elif 'email' in contact_method['type']:
            sys.stdout.write("Email:  ")
            sys.stdout.write(contact_method['address'])
        elif 'push_notification' in contact_method['type']:
            sys.stdout.write("Push:  ")
            sys.stdout.write(contact_method['label'])
        sys.stdout.write("\n")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves contact info for all "
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    get_users(session)
