#!/usr/bin/env python

import argparse
from pdpyras import APISession, PDClientError
import csv

# Disables noisy warning logging from pdpyras
import logging
logging.disable(logging.WARNING)

# Get all users' contact methods.
# Originally by Ryan Hoskin

def get_users(session, args):
    tf = None
    if args.csv_file:
        tf = csv.writer(args.csv_file)
        print("Creating / Clearing : %s\n"%(args.csv_file.name))
        tf.writerow(['User', 'Phone', 'SMS', 'Email', 'Push'])
    else:
        print("Listing All Users' Contact Methods:\n")
    try:
        for user in session.iter_all('users'):
            print_contact_methods(user, session, tf)
    except PDClientError as e:
        raise e

def print_contact_methods(user, session, csv):
    contacts = {
        'phone': None,
        'sms': None,
        'email': None,
        'push': None,
    }
    for contact_method in session.rget('users/%s/contact_methods'%user['id']):
        if 'phone' in contact_method['type']:
            contacts['phone'] = '%s %s'%(contact_method['country_code'], contact_method['address'])
        elif 'sms' in contact_method['type']:
            contacts['sms'] = '%s %s'%(contact_method['country_code'], contact_method['address'])
        elif 'email' in contact_method['type']:
            contacts['email'] = contact_method['address']
        elif 'push_notification' in contact_method['type']:
            contacts['push'] = contact_method['label']
    if csv:
        csv.writerow([user['name'], contacts['phone'], contacts['sms'], contacts['email'], contacts['push']])
        print("Added %s to csv."%(user['name']))
    else:
        print("User: %s"%(user['name']))
        print("Phone: %s"%(contacts['phone'])) if contacts['phone'] else None
        print("SMS: %s"%(contacts['sms'])) if contacts['sms'] else None
        print("Email: %s"%(contacts['email'])) if contacts['email'] else None
        print("Push: %s"%(contacts['push'])) if contacts['push'] else None
        print("-----")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Retrieves contact info for all "
        "users in a PagerDuty account")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-f', '--csv-file', required=False,
        default=False, type=argparse.FileType('w'), help="Output to a csv file")
    args = ap.parse_args()
    session = APISession(args.api_key)
    get_users(session, args)
