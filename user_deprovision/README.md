# PagerDuty User De-Provision

Python script to de-provision a user in PagerDuty including removing them from all schedules, escalation policies, and teams that they are a part of. The affected resources are logged and printed to the console.

Original script by Lucas Epp ([lfepp/pd_user_deprovision](https://github.com/lfepp/pd_user_deprovision)); refactored for long-term maintenance and support by Demitri Morgan <demitri@pagerduty.com>.

## Usage

This script is meant to be used as a command line tool with the following arguments:

`./user_deprovision.py --access-token ENTER_PD_ACCESS_TOKEN --users-emails-from-csv ./emails-to-remove.csv --from-email user-requesting-deletion@example.com`

`-a`, `--access-token`: A valid PagerDuty v2 REST API access token from your account

`-u`, `--users-emails-from-csv`: A csv file of the PagerDuty email address(es) for the user(s) you want to delete from your account

`-f`, `--from-header`: The PagerDuty email address of the user that is requesting the deletion

### Optional arguments

`-v`, `--verbose`: output the logs to the console while running

`-b`., `--backup`: backup info about each user to a json file

`-y`, `--delete-yes-to-all`: by default the script will ask you before deleting _each user_, which can be tedious for 
large data sets.

`-r`, `-auto-resolve-incidents`: when the script encounters a user that has open incidents, it will pause and 
ask if you'd like to resolve those incidents. If you do not resolve all incidents associated with a user, the user will
not be successfully deleted. 

`-n`, `--do-not-delete-users`: Completely remove users from all schedules, escalation policies, and teams that they are a part of, but will not remove user from account.

## Notes and Caveats

**If you do not resolve all incidents associated with a user, the user will not be successfully deleted.**

You might see a 400 error when removing a user from the team, but this error itself is sometimes erroneous. If the log output shows that the user wasn't successfully removed from the team, but was successfully deleted, you can trust the latter information and ignore the former. 

## Author

Luke Epp <lucas@pagerduty.com>

## Maintainer

PagerDuty Support <support@pagerduty.com>
