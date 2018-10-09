#!/usr/bin/env python

import argparse
import sys
import pdpyras

def no_sms(token):
    session = pdpyras.APISession(token)
    users = session.iter_all(
        'users',
        params={'include[]':['contact_methods', 'notification_rules']}
    )
    for user in users:
        for rule in user['notification_rules']:
            if rule['contact_method']['type'] == 'sms_contact_method':
                print('{name}: deleting notification rule {id}'.format(**{
                    'name': user['name'],
                    'id': rule['id']
                }))
                session.delete(rule['self'])
        for method in user['contact_methods']:
            if method['type'] == 'sms_contact_method':
                print('{name}: deleting contact method {id}'.format(**{
                    'name': user['name'],
                    'id': method['id']
                }))
                session.delete(method['self'])

if __name__=='__main__':
    ap=argparse.ArgumentParser(description="Sweeps through an account and "
        "deletes all of the user contact methods and notification rules that "
        "are SMS-based.")
    ap.add_argument("api_key", help="REST API key")
    args = ap.parse_args()
    no_sms(args.api_key)
