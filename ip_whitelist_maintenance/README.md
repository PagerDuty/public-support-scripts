# PagerDuty IP Address Whitelist Maintenance

These scripts are designed to be run via a cron job, to help maintain ACLs that specifically permit PagerDuty-controlled IP addresses.

The shell scripts should have their MAILTO variable set to generate an email(or any other notification method) when output occurs. Output will occur when an IP is added/removed or changed for the service you are checking.

* `check_events.sh` - Checks events.pagerduty.com for changed IP addressses.
* `check_mailservers.sh` - Checks acme.pagerduty.com for changed MX record IP addressses.
(Used when you utilize an email integrated service and need to whitelist outgoing traffic to PagerDuty)
* `check_webhooks.sh` - Checks webhooks.pagerduty.com for changed IP addressses.
* `check_webhooks_and_alert.sh` - Same as `check_webhooks.sh` but triggers a PagerDuty incident.
* `update_ec2_pd_webhook_ip_security_group.py`: clear out and repopulate a specified AWS Security Group with rules permitting TCP access to 1-2 ports to PagerDuty IP addresses. Pulls 

These scripts were originally created by Matt Collins and Demitri Morgan:

* https://github.com/mdcollins05/PD-IP-Checker
* https://gist.github.com/Deconstrained/f29fe709f8e4ff28715f7cf715e80f13
