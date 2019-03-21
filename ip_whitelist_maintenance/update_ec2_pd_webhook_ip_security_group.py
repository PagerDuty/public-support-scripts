#!/usr/bin/env python

import argparse
import logging
import requests
import subprocess
import sys

from boto.ec2 import get_region
from boto.ec2.connection import EC2Connection

log = logging.getLogger('pdip')

def main():
    ap = argparse.ArgumentParser(description="Clear and repopulate an AWS EC2 "
        "security group's rules such that all TCP traffic from PagerDuty "
        "outbound integration source IP addresses is permitted.")
    ap.add_argument('-i', '--aws-access-key-id', type=str, required=True)
    ap.add_argument('-k', '--aws-secret-access-key', type=str, required=True)
    ap.add_argument('-r', '--region', type=str, default='us-east-1',
        help="AWS region in which to find the security group.")
    ap.add_argument('-p', '--dst-ports', type=str, default='80,443', 
        help="Comma-delineated list of ports to which PagerDuty will be "
        "granted access.")
    ap.add_argument('-v', '--verbose', default=False, action='store_true',
        help="Show verbose output")
    ap.add_argument('security_group_id', type=str)
    args = ap.parse_args()
    ports = [int(p) for p in args.dst_ports.split(',') if p.isdigit()]
    if not ports:
        print("No valid destination ports specified.")
        sys.exit(1)
    if args.verbose:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)

    conn = EC2Connection(aws_access_key_id=args.aws_access_key_id,
        aws_secret_access_key=args.aws_secret_access_key,
        region=get_region(args.region))
    pagerduty_ips = set([])
    for ip in requests.get('https://app.pagerduty.com/webhook_ips').json():
        pagerduty_ips.add(ip+'/32')

    empty = False
    while not empty:
        # boto does not return more than X rules at a time, so let's re-download
        # the data, revoke rules and check for a clean slate until it's truly
        # empty. Without this loop, AWS will spit out 400's ("specified rule
        # already exists")
        groups = conn.get_all_security_groups(group_ids=[args.security_group_id])
        if not groups:
            print("No group found matching ID")
            sys.exit(1)
        group  = groups[0]
        # Clear out existing rules:
        rules = list(group.rules)
        empty = not len(rules)
        for rule in rules:
            for grant in rule.grants:
                log.info("Revoking %s access to port %d-%d from %s",
                    rule.ip_protocol, int(rule.from_port), int(rule.to_port),
                    grant.cidr_ip)
                group.revoke(ip_protocol=rule.ip_protocol,
                    from_port=rule.from_port, to_port=rule.to_port,
                    cidr_ip=grant.cidr_ip)
    # Add rules to permit PagerDuty IPs for each port given
    for port in ports:
        log.info("Authorizing IPs access to port %d", port)
        group.authorize(ip_protocol='tcp', from_port=port, to_port=port,
            cidr_ip=list(pagerduty_ips))


    
if __name__ == '__main__': 
    main()
