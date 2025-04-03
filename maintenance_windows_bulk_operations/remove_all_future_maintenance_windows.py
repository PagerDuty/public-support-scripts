#!/usr/bin/env python

import argparse
import pagerduty


def remove_all_future_maintenance_windows(args):
    session = pagerduty.RestApiV2Client(args.api_key)
    progress_printer = lambda o, i, n: (print("Deleting %d/%d: %s"%(
        i, n, o['summary']
    )))
    mw_params = {"filter":"future"}
    if len(args.service_ids):
        mw_params['service_ids[]'] = args.service_ids

    for mw in session.iter_all("maintenance_windows",
            item_hook=progress_printer, params=mw_params, total=True):
        if args.dry_run:
            continue
        try:
            session.delete(mw['self'])
        except Error as e:
            message = "API Error: %s"%e
            if e.response is not None:
                message += " HTTP %d: %s"%(e.response.status_code,
                    e.response.text)
            print(message)
            continue
    if args.dry_run:
        print("(Didn't actually delete anything, since -n/--dry-run was given)")

def main(argv=None):
    ap = argparse.ArgumentParser(description="Deletes all future maintenance "
        "windows in a PagerDuty account. Useful for when an automated process "
        "for creating maintenance windows was used incorrectly or errored.")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-s', '--service', dest='service_ids', action='append',
        default=[], help="One or more service IDs to which the deletion should "
        "be limited. Note, if unspecified, MAINTENANCE WINDOWS FOR ALL "
        "SERVICES will be deleted.")
    ap.add_argument('-n', '--dry-run', default=False, action='store_true',
        help="Don't perform any action; instead, show the maintenance windows "
        "that would be deleted.")
    args = ap.parse_args()
    remove_all_future_maintenance_windows(args)

if __name__=='__main__':
    main()
