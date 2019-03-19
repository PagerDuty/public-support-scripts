#!/usr/bin/env python

import argparse
import csv
import pdpyras

def semicolonize(l):
    return ';'.join([i['summary'].replace(';', r'\;') for i in l])

def write_users(users_dict, uid_list, filename):
    """
    Write a list of users to a CSV file.

    The columns are:
    - User ID
    - User name
    - User email
    - semicolon-delimited list of teams they are a member of

    :param users_dict:
        Dictionary of users keyed by ID
    :param uid_list:
        List of user IDs to include
    :param filename:
        Name of the file to write to
    """
    uw = csv.writer(open(filename, 'w'))
    for uid in uid_list:
        u = users_dict[uid]
        uw.writerow([
            uid,
            u['summary'],
            u['name'],
            u['email'], 
            semicolonize(u['teams'])
        ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-k', '--api-key', help="A full-access, admin-level REST "
        "API key", required=True)
    args = ap.parse_args()
    s = pdpyras.APISession(args.api_key)
    # Go through all EPs
    print("Fetching users...")
    all_users_dict  = s.dict_all('users', params={
        'include[]':['teams', 'notification_rules']
    })
    print("Fetching escalation policies...")
    all_eps_dict = s.dict_all('escalation_policies', params={
        'include[]':['targets', 'teams']
    })
    all_users = set(all_users_dict)
    n_users = len(all_users_dict)
    users_offcall = set(all_users_dict)
    users_onenotif = set(all_users_dict)
    eps_onelevel = set({})
    eps_multilevel = set({})

    print("Checking escalation policies for on-call users...")
    # Check EPs for on-call users
    for (i, e) in all_eps_dict.items():
        if len(e['escalation_rules']) > 1:
            eps_multilevel.add(i)
        else:
            eps_onelevel.add(i)
        for rule in e['escalation_rules']:
            for target in rule['targets']:
                if target['type'].startswith('user'):
                    users_offcall -= set([user['id']])
                elif target['type'].startswith('schedule'):
                    sched = s.rget(target['self'])
                    for user in sched['users']:
                        users_offcall -= set([user['id']])

    # Check users for the number of notification rules
    for (i, u) in all_users_dict.items():
        if len(u['notification_rules']) > 2:
            users_onenotif.remove(i)
    users_twoplus_notifs = all_users - users_onenotif
    users_oncall = all_users - users_offcall

    n_oncall = len(users_oncall)
    n_onelevel = len(eps_onelevel)
    n_multilevel = len(eps_multilevel)

    print("USERS: %d are on-call (%3.2f%%)"%(n_oncall, n_oncall*100./n_users))
    print("ESCALATION POLICIES: %d have >1 level (%3.2f%%)"%(
        n_multilevel,
        n_multilevel*100./(n_multilevel+n_onelevel)
    ))

    print("Writing data to files...")
    ep_fn = 'single-level-eps.csv'
    epw = csv.writer(open(ep_fn, 'w'))
    for epid in eps_onelevel:
        ep = all_eps_dict[epid]
        epw.writerow([
            epid,
            ep['summary'],
            semicolonize(ep['teams'])
        ])
    write_users(all_users_dict, users_offcall, 'users-not-on-call.csv')
    write_users(all_users_dict, users_onenotif, 'users-two-or-fewer-nr.csv')
    print("Done")


if __name__ == '__main__':
    try:
        main()
    except pdpyras.PDClientError as e:
        if e.response is not None:
            print(e.response.text)
