#!/usr/bin/env python

# PagerDuty Support asset: mass_update_incidents
from typing import Dict, Union, List
import argparse
import sys

import pagerduty
import time

# Default parameters:
PARAMETERS: Dict[str, Union[str, List[str]]] = {
    'exclude': ['escalation_policies', 'impacted_services', 'pending_actions', 'last_status_change_by', 'responders',
                'alert_grouping', 'conference_bridges']
}
MAX_INCIDENTS = 10000   # Maximum number of incidents to retrieve in one request, based on Python-Pagerduty SDK limits.
BATCH_SIZE = 100        # Maximum number of incidents to update in one batch request.
BASE_RATE = 100.0       # Base rate of alert processing (alerts per second)
ALERT_THRESHOLD = 100   # Threshold above which we apply progressive rate limiting


def mass_update_incidents(args):
    session = pagerduty.RestApiV2Client(args.api_key, default_from=args.requester_email)
    session.headers.update({"X-SOURCE-SCRIPT": "public-support-scripts/mass_update_incidents"})

    if args.user_id:
        PARAMETERS['user_ids[]'] = args.user_id.split(',')
        print("Acting on incidents assigned to user(s): " + args.user_id)
    if args.service_id:
        PARAMETERS['service_ids[]'] = args.service_id.split(',')
        print("Acting on incidents corresponding to service ID(s): " +
              args.service_id)
    if args.action == 'resolve':
        PARAMETERS['statuses[]'] = ['triggered', 'acknowledged']
        print("Resolving incidents")
    elif args.action == 'acknowledge':
        PARAMETERS['statuses[]'] = ['triggered']
        print("Acknowledging incidents")
    if args.date_range is not None:
        sinceuntil = args.date_range.split(',')
        if len(sinceuntil) != 2:
            raise ValueError("Date range must be two ISO8601-formatted time "
                             "stamps separated by a comma.")
        PARAMETERS['since'] = sinceuntil[0]
        PARAMETERS['until'] = sinceuntil[1]
        print("Getting incidents for date range: " + " to ".join(sinceuntil))
    else:
        PARAMETERS['date_range'] = 'all'
        print("Getting incidents of all time")
    print("Parameters: " + str(PARAMETERS))
    if args.incident_id:
        PARAMETERS['incident_ids[]'] = args.incident_id.split(',')
        if len(PARAMETERS['incident_ids[]']) > MAX_INCIDENTS:
            raise ValueError(
                f"You can only update a maximum of {MAX_INCIDENTS} incidents at a time. Received list of {len(PARAMETERS['incident_ids[]'])} incidents.")
    try:
        if args.incident_id:
            if args.action == 'resolve':
                # If resolving incidents, we need to fetch the incident details for the alert counts
                # Fetch incident bodies in bulk using the bulk update endpoint
                print(f"Fetching details for {len(PARAMETERS['incident_ids[]'])} incidents. Please be patient as this "
                      "can take a while for large volumes...")
                incident_references = []
                for incident_id in PARAMETERS['incident_ids[]']:
                    incident_references.append({"id": incident_id, "type": "incident_reference"})

                # Make bulk request to get incident details
                response = session.rput("/incidents", json={
                    "incidents": incident_references
                }, params=PARAMETERS)
                incidents = response.get('incidents', [])
                print(f"Successfully fetched {len(incidents)} incident details")
            else:
                # For acknowledging, we don't need to fetch incident details
                incidents = [{'id': incident_id, 'type': 'incident_reference'} for incident_id in PARAMETERS['incident_ids[]']]
        else:
            print("Please be patient as this can take a while for large volumes "
                  "of incidents.")
            incidents = session.list_all('incidents', params=PARAMETERS)

        total_incidents = len(incidents)
        print(f"Processing {total_incidents} incidents in batches of {BATCH_SIZE}")
        
        if args.dry_run:
            if args.action == 'acknowledge':
                print(f"[DRY RUN] Would acknowledge {total_incidents} incidents")
            else:
                # Count total alerts in all incidents
                total_triggered_alerts = sum(incident.get('alert_counts', {}).get('triggered', 0) for incident in incidents)
                print(f"[DRY RUN] Would resolve {total_incidents} incidents with {total_triggered_alerts} total triggered alerts")
            return
        
        # Calculate total number of batches
        num_batches = (total_incidents + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Process incidents in batches
        for batch_num in range(num_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_incidents)
            batch = incidents[start_idx:end_idx]
            
            # Process this batch
            if args.action == 'acknowledge':
                # For acknowledging, we can just do a bulk update
                print(f"Batch {batch_num + 1}/{num_batches}: Acknowledging {len(batch)} incidents")
                
                incident_updates = list(map(lambda incident: {
                    "id": incident['id'],
                    "type": "incident_reference",
                    "status": "acknowledged"
                }, batch))
                
                # Send bulk update request
                start_time = time.time()
                session.rput("/incidents", json={
                    "incidents": incident_updates
                })
                processing_time = time.time() - start_time

                # Wait for 1 second between batches
                wait_time = 1.0
                print(f"  Batch completed in {processing_time:.2f}s, waiting {wait_time:.2f}s before next batch")
                time.sleep(wait_time)
                
            else:
                # For resolving, we need to calculate total alerts and adjust rate
                batch_triggered_alerts = sum(incident.get('alert_counts', {}).get('triggered', 0) for incident in batch)
                print(f"Batch {batch_num + 1}/{num_batches}: Resolving {len(batch)} incidents with {batch_triggered_alerts} total triggered alerts")
                
                # Prepare bulk update request for non-skipped incidents
                incident_updates = list(map(lambda incident: {
                    "id": incident['id'],
                    "type": "incident_reference",
                    "status": "resolved"
                }, batch))
                
                # Send bulk update request and measure time
                start_time = time.time()
                session.rput("/incidents", json={
                    "incidents": incident_updates
                })
                processing_time = time.time() - start_time
                
                # Calculate minimum time needed based on alert count and rate limit
                min_time_needed = batch_triggered_alerts / 100.0
                
                # Calculate dynamic rate multiplier based on alert count
                # For small numbers of alerts, use minimal multiplier
                # For large numbers, apply progressively larger multiplier
                if batch_triggered_alerts <= ALERT_THRESHOLD:
                    # For small batches, use a small fixed multiplier (1.5x)
                    dynamic_multiplier = 1.5
                else:
                    # For larger batches, scale up the multiplier based on alert count
                    # Formula: 1.5 + (alerts - threshold) / threshold 
                    # Examples: 
                    # - At threshold of 200: 200 alerts → 1.5x, 400 alerts → 2.5x, 600 alerts → 3.5x
                    excess_alerts = batch_triggered_alerts - ALERT_THRESHOLD
                    dynamic_multiplier = 1.5 + (excess_alerts / ALERT_THRESHOLD)
                    # Cap the multiplier at a reasonable maximum (5.0)
                    dynamic_multiplier = min(dynamic_multiplier, 5.0)
                
                # Apply the dynamic multiplier to account for backend async work
                adjusted_time_needed = min_time_needed * dynamic_multiplier
                
                # Calculate wait time (adjusted time minus the time already spent processing)
                wait_time = max(1.0, (adjusted_time_needed - processing_time))
                
                print(f"  Batch completed in {processing_time:.2f}s, {batch_triggered_alerts} alerts")
                print(f"  Dynamic rate multiplier: {dynamic_multiplier:.2f}x (based on alert count)")
                print(f"  Rate limit: {adjusted_time_needed:.2f}s needed")
                print(f"  Waiting {wait_time:.2f}s before next batch to maintain rate limit")
                time.sleep(wait_time)
    except pagerduty.Error as e:
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error: {str(e)}")
            if hasattr(e.response, 'text'):
                print(e.response.text)
        raise e


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mass ack or resolve incidents "
                                             "either corresponding to a given service, or assigned to a given "
                                             "user. Note, if you are trying to update over 10k incidents at a "
                                             "time, you should set the --date-range argument to a lesser interval "
                                             "of time and then run this script multiple times with a different "
                                             "interval each time until the desired range of time is covered.")
    ap.add_argument('-d', '--date-range', default=None, help="Only act on "
                                                             "incidents within a date range. Must be a pair of ISO8601-formatted "
                                                             "time stamps, separated by a comma, representing the beginning (since) "
                                                             "and end (until) of the date range. By default, incidents of all time "
                                                             "will be updated.")
    ap.add_argument('-k', '--api-key', required=True, help="REST API key")
    ap.add_argument('-n', '--dry-run', default=False, action='store_true',
                    help="Do not perform the actions but show what will happen.")
    ap.add_argument('-i', '--incident-id', default=None, help="Id of the "
                                                              "incident, or comma separated list of incidents to be updated")
    ap.add_argument('-s', '--service-id', default=None, help="ID of the "
                                                             "service, or comma-separated list of services, for which incidents "
                                                             "should be updated; leave blank to match all services.")
    ap.add_argument('-u', '--user-id', default=None, help="ID of user, "
                                                          "or comma-separated list of users, whose assigned incidents should be "
                                                          "included in the action. Leave blank to match incidents for all users.")
    ap.add_argument('-a', '--action', default='resolve', choices=['acknowledge',
                                                                  'resolve'],
                    help="Action to take on incidents en masse")
    ap.add_argument('-e', '--requester-email', required=True, help="Email "
                                                                   "address of the user who will be marked as performing the actions.")
    args = ap.parse_args()
    mass_update_incidents(args)


if __name__ == '__main__':
    sys.exit(main())
