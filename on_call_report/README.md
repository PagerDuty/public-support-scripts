# On-call Users Report

This script generates a report on your PagerDuty account to answer the following questions about all on-call personnel and policies:

1. **On-call Representation:**
    * What portion of users are on-call, i.e. what percentage/which users are part of an escalation policy (via a schedule or as an individual user)?
    * Which users are _not_ on-call, and which team are they associated with?
2. **Escalation Policy Utilization:**
    * What percent of escalation policies have multiple levels?
    * Which escalation policies have only one level, and what team(s) are they associated with?
3. **Notification Rule Best-Practices:** 
    * How many users have more than two notification rules, and what teams are they on?
    * Which users _do not_ have more than two notification rules?

## Usage

Run the script as follows, using an admin-level REST API key. As of this version it is not possible to use this script with the coverage of its report scoped to an individual team.

```
./oncall_report.py -k API-KEY-HERE
```

After it is finished running, it will create three files:

* `results.txt`: A plain text file with basic statistics printed to it
* `users-not-on-call.csv`: a CSV with columns as follows: User ID, user name, user email, list of associated teams
* `single-level-eps.csv`: a CSV file with columns as follows: escalation policy ID, escalation policy name, list of associated teams
* `users-two-or-fewer-nr.csv`: a CSV file with columns as followss: User ID, user name, user email, list of associated teams.

Note, the lists of teams are semicolon-delimited.
