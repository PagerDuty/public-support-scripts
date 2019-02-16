# PagerDuty User De-Provision

Python script to de-provision a user in PagerDuty including removing them from all schedules, escalation policies, and teams that they are a part of. The affected resources are logged and printed to the console.

Original script by Lucas Epp ([lfepp/pd_user_deprovision](https://github.com/lfepp/pd_user_deprovision)); refactored for long-term maintenance and support by Demitri Morgan <demitri@pagerduty.com>.

## Usage

This script is meant to be used as a command line tool with the following arguments:

`./user_deprovision.py --access-token ENTER_PD_ACCESS_TOKEN --user-email user-to-delete@example.com --from-email user-requesting-deletion@example.com`

**-a**, **--access-token**: A valid PagerDuty v2 REST API access token from your account

**-u**, **--user-email**: The PagerDuty email address for the user you want to delete from your account

**-f**, **--from-header**: The PagerDuty email address of the user that is requesting the deletion

## Author

Luke Epp <lucas@pagerduty.com>

## Maintainer

PagerDuty Support <support@pagerduty.com>
