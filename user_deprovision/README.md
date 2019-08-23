# PagerDuty User De-Provision

Python script to de-provision a user in PagerDuty including removing them from all schedules, escalation policies, and teams that they are a part of. The affected resources are logged and printed to the console.

Original script by Lucas Epp ([lfepp/pd_user_deprovision](https://github.com/lfepp/pd_user_deprovision)); refactored for long-term maintenance and support by Demitri Morgan <demitri@pagerduty.com>.

## Usage

This script is meant to be used as a command line tool with the following arguments:

`./user_deprovision.py --access-token ENTER_PD_ACCESS_TOKEN --user-email user-to-delete@example.com --from-email user-requesting-deletion@example.com`

**-a**, **--access-token**: A valid PagerDuty v2 REST API access token from your account

**-u**, **--user-email**: The PagerDuty email address for the user you want to delete from your account

**-f**, **--from-header**: The PagerDuty email address of the user that is requesting the deletion

## Notes and Caveats

You might see a 400 error when removing a user from the team, but this error itself is sometimes erroneous. If you the log output shows that the user wasn't successfully removed from the team, but was successfully deleted, you can trust the latter information and ignore the former. 

## Author

Luke Epp <lucas@pagerduty.com>

## Maintainer

PagerDuty Support <support@pagerduty.com>
