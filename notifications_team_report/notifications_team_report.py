#!/usr/bin/env python

import argparse
import codecs
import csv
import datetime
import json
import logging
import pickle
import sys
import time

import pdpyras

def ascii_keys(data):
    return dict((k.encode('ascii'), v) for (k, v) in data.items())

def print_progress(result, i, n):
    new_percent = int(100.*i/n)
    prev_percent = int(100.*(i-1.)/n)
    if new_percent != prev_percent:
        logging.info("Getting data: %d%% (%d of %d)", new_percent, i, n)

def main():
    # Memoizing dictionaries
    api = None
    notifs = []
    stats = {}
    teams = {}

    ap = argparse.ArgumentParser(
        description="Generates notification reports for each team. A work-"
        "around for how notification reports in analytics cannot yet provide a "
        "per-team drilldown nor generate the report according to the team lens."
    )
    ap.add_argument('-i', '--interval', dest='n_days', type=int, default=30,
        help="Specify a number of days back in history over which to generate\
        the report.")
    ap.add_argument('-r', '--resume-file', dest='resume_file', default=False,
        type=argparse.FileType('rb'), help="Read previous ILE data from this\
        file instead of retrieving it from the API.")
    ap.add_argument('-v', dest='verbosity', action='count', default=0,
        help="Logging verbosity (default: INFO-level messages).")
    ap.add_argument('-w', '--write-file', dest='write_file', default=False,
        type=argparse.FileType('wb'), help="A cache file to use for saving ILE\
        data that can be resumed from, before generating the reports. Useful\
        for if there's a massive quantity of ILE data to be saved, as a\
            safeguard in case something goes wrong in the reporting part.")
    ap.add_argument('-k', '--api-key', type=str, required=True, 
        dest='api_key', help="REST API key")
    args = ap.parse_args()
    loglevs = ['info', 'critical', 'error', 'warning', 'info', 'debug']
    loglev = min(args.verbosity, 5)
    logging.basicConfig(
        level=[getattr(logging, l.upper()) for l in loglevs][loglev],
        stream=sys.stdout
    )

    now_s = int(time.time())
    if args.resume_file:
        notifs, teams = pickle.load(args.resume_file)
    else:
        api = pdpyras.APISession(args.api_key)

        if 'teams' not in api.rget('/abilities'):
            logging.error("This account doesn't have the \"teams\" \ ability! "\
                "Why are you even running this script?"
            )
            return

        logging.info("Retrieving notification log entries...")
        now = datetime.datetime.now() 
        more = True 
        offset = 0
        params = {
            'since': (now-datetime.timedelta(args.n_days)).isoformat(),
            'until': now.isoformat(),
            'include[]': ['channels'],
        }
        for ile in api.iter_all('log_entries', params=params, total=True,
                item_hook=print_progress):
            if 'notify_log_entry' in ile['type']:
                ile_teams = ile['teams']
                index = len(notifs)
                for team in ile_teams:
                    teams.setdefault(team['summary'],[])
                    teams[team['summary']].append(index)
                notifs.append(ile)
                logging.debug("Adding log entry: ID=%s", ile['id'])
            else:
                logging.debug("Skipping log entry because it's not a "\
                    "notification log entry, but %s: ID=%s", ile['type'], 
                    ile['id'])
        if args.write_file:
            logging.info("Writing log entry data to file...")
            pickle.dump((notifs, teams), args.write_file)

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
            channel = ile['channel']
            if 'notification' in channel and 'user' in ile:
                notification = channel['notification']
                notif_type = None
                if 'push' in notification['type']:
                    notif_type = 'push'
                elif notification['type'] in stats[team]:
                    notif_type = notification['type']
                else:
                    logging.error("Invalid/unrecognized notification channel \
                        type: %s", notification['type'])
                if notif_type:
                    stats[team][notif_type] += 1
                    stats[team]['total'] += 1
                    
                    print( 
                        ile['created_at'],
                        notif_type,
                        notification['address'],
                        ile['user']['summary']
                    )

                    notifsw.writerow([
                        ile['created_at'].encode('ascii', 'ignore'),
                        notif_type.encode('ascii', 'ignore'),
                        notification['address'].encode('ascii', 'ignore'),
                        ile['user']['summary'].encode('ascii', 'ignore')
                    ])
                logging.debug("Added notification log entry: %s",
                    str(ile))
            else:
                logging.warn("Notification log entry contains no notification "\
                 " or user! %s", json.dumps(ile, indent=4))
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
