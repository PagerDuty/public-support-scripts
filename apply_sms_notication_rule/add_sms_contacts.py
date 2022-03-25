#!/usr/bin/env python

import argparse
import pdpyras

def add_sms(token):
    session = pdpyras.APISession(token)
    users = session.iter_all(
        'users',
        params={'include[]':['contact_methods', 'notification_rules']}
    )
    for user in users:
        print(f"Starting user: {user.get('id')}")
        self = user.get('self')
        contacts = {}
        contact_methods = user.get('contact_methods')
        # Loop contacts_methods and get mobile number
        # If multiply SMS listed will use first listed
        # If multiply Phones listed will use last listed
        print(f"Checking user's contact methods.")
        for method in contact_methods:
            if method['type'] == 'sms_contact_method' and method.get('summary') == 'Mobile':
                contacts['sms'] = method.get('address')
                contacts['sms_id'] = method.get('id')
                contacts['country_code'] = method.get('country_code')
                break
            if method.get('type') == 'phone_contact_method' and method.get('summary') == 'Mobile':
                contacts['phone'] = method.get('address')
                contacts['country_code'] = method.get('country_code')

        # Check user has mobile phone but now SMS mobile update profile
        if not contacts.get('phone') and not contacts.get('sms_id'):
            print(f"Skipping user: {user.get('id')}, no phone or sms number")
            continue
        elif contacts.get('phone') and not contacts.get('sms_id'):
            res_contact = session.post(self + '/contact_methods', json={
                "contact_method": {
                    "type": "sms_contact_method",
                    "summary": "Mobile",
                    "country_code":contacts.get('country_code'),
                    "label": "Mobile",
                    "address": contacts.get('phone')
                }
            })
            if res_contact.ok:
                add_contact = res_contact.json()['contact_method']
                contacts['sms_id'] = add_contact.get('id')
            else:
                print(res_rule.text)
                print(f"Failed to update contact for user, {user.get('id')}.")
                continue

        # Add SMS to  user has mobile phone but now SMS mobile update profile
        if contacts.get('sms_id'):
            print(f"Adding SMS to users notication rules.")
            update = True
            for rule in user.get('notification_rules'):
                start = rule.get('start_delay_in_minutes')
                rule_contact_method = rule.get('contact_method')
                rule_type = rule_contact_method.get('type')
                if rule_type == 'sms_contact_method' and start == 0:
                    update = False
                    print(f"Skipping adding rule, user already has SMS immediately rule")
            if update:
                res_rule = session.post(self + '/notification_rules', json={
                    "notification_rule": {
                        "type": "assignment_notification_rule",
                        "start_delay_in_minutes": 0,
                        "contact_method": {
                            "id": contacts.get('sms_id'),
                            "type": "sms_contact_method"
                        },
                    }
                })
                if res_rule.ok:
                    print("rule added")

if __name__=='__main__':
    ap=argparse.ArgumentParser(description="Sweeps through an account and "
        "add mobile phone to as SMS number and adds SMS to notification rules.")

    helptxt = "PagerDuty full-access REST API key"
    ap.add_argument('-k', '--api-key', required=True, help=helptxt)
    args = ap.parse_args()
    add_sms(args.api_key)
