#!/usr/bin/env python

import argparse
import csv
import datetime
import logging
import sys
import time

import pdreq

# Memoizing dictionaries
api = None
notifs = []
stats = {}
teams = {}

def main():
    global api
    ap = argparse.ArgumentParser(
        description="Generates notification reports for each team."
    )
    ap.add_argument('-i', '--interval', dest='n_days', type=int, default=30,
        help="Specify a number of days back in history over which to generate\
        the report.")
    ap.add_argument('-v', dest='verbosity', action='count', default=0,
        help="Logging verbosity (default: INFO-level messages).")
    ap.add_argument('token', type=str, help="A v2 REST API key to use for\
        accessing notifications. A read-only key should suffice.")
    args = ap.parse_args()
    loglevs = ['info', 'critical', 'error', 'warning', 'info', 'debug']
    loglev = min(args.verbosity, 5)
    logging.basicConfig(
        level=[getattr(logging, l.upper()) for l in loglevs][loglev],
        stream=sys.stdout
    )

    api = pdreq.APIConnection(args.token)

    abilities_resp = api.get('/abilities')
    if abilities_resp.status_code // 100 != 2:
        logging.critical(
            'API authentication error (status=%d): %s', 
            ile_resp.status_code,
            ile_resp.text
        )
        return

    if 'teams' not in abilities_resp.json()['abilities']:
        logging.error(
"This account doesn't have the \"teams\" \ ability! Why are you even running \
this script?"
        )
        return

    logging.info("Retrieving notification log entries...")
    now_s = int(time.time())
    now = datetime.datetime.now() 
    more = True 
    offset = 0
    params = {
        'total': 'true',
        'limit': 100,
        'since': (now-datetime.timedelta(args.n_days)).isoformat(),
        'until': now.isoformat(),
        'include[]': ['channels'],
    }
    while more:
        params['offset'] = offset
        ile_resp = api.get('/log_entries', params=params)
        ile_bod = ile_resp.json() 
        for ile in ile_bod['log_entries']:
            if 'notify_log_entry' in ile['type']:
                ile_teams = ile['teams']
                index = len(notifs)
                for team in ile_teams:
                    teams.setdefault(team['summary'],[])
                    teams[team['summary']].append(index)
                notifs.append(ile)
        more = ile_bod['more']
        offset += 100

    # Tally up for each team and write to file
    for (team, ile_indices) in teams.items():
        stats.setdefault(team, {
            'email':0, 'phone':0, 'sms':0, 'push':0, 'total':0
        })
        team_file = '%s_%d.csv'%(team, now_s)
        csvf = open(team_file, 'w')
        notifsw = csv.writer(csvf)
        for index in reversed(ile_indices):
            ile = notifs[index]
            if 'notification' in ile:
                notif_type = None
                if 'push' in ile['notification']['type']:
                    notif_type = 'push'
                elif ile['notification']['type'] in stats['team']:
                    notif_type = ile['notification']['type']
                else:
                    logging.error(("Invalid/unrecognized notification channel "+
                        "type: %s"), ile['notification']['type'])
                if notif_type: 
                    stats[team][notif_type] += 1
                    stats[team]['total'] += 1
                    
                    notifsw.writerow([
                        ile['created_at'],
                        notif_type,
                        ile['notification']['address'],
                        ile['agent']['summary']
                    ])
        csvf.close()
        logging.info("Wrote list of notifications for team to %s", team_file)

    stats_file = 'notif_totals_%d.csv'%now_s
    csvf = open(stats_file, 'w')
    statsw = csv.DictWriter(
        csvf, 
        ['team', 'email', 'sms', 'phone', 'push', 'total']
    )
    for (team, team_stats) in stats.items():
        team_stats['team'] = team
        statsw.writerow(team_stats)
    csvf.close()
    if len(stats.values()):
        logging.info("Wrote stats to %s", stats_file)
    else:
        logging.warn("No data written; no team-specific notifications.")


if __name__ == '__main__':
    main() 
