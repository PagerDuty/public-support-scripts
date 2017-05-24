#!/usr/bin/env python
"""
no_sms.py

This sweeps through an account and deletes all of the user contact methods and
notification rules that are SMS-based.
"""

import pdreq
import sys


def no_sms(token):
    api = pdreq.APIConnection(token)
    users = api.get_all(
        'users',
        params={'include[]':['contact_methods', 'notification_rules']}
    )
    for user in users:
        for rule in user['notification_rules']:
            if rule['contact_method']['type'] == 'sms_contact_method':
                print '{name}: deleting notification rule {id}'.format(**{
                    'name': user['name'],
                    'id': rule['id']
                })
                api.delete(rule['self'])
        for method in user['contact_methods']:
            if method['type'] == 'sms_contact_method':
                print '{name}: deleting contact method {id}'.format(**{
                    'name': user['name'],
                    'id': method['id']
                })
                api.delete(method['self'])



if __name__=='__main__':
    if len(sys.argv) < 2:
        print "Required argument (API token) missing."
    no_sms(sys.argv[1].strip())
