## Alerts ##
### Download Alerts to CSV
```get_alerts_csv.py``` https://gist.github.com/danquixote/5ba09f3fcacd284c111f

A sample script to programatically access the PD alerts csv-page behind the login, via a single-session.

### Alert Volume/Pain for On-Call Users
```alert_volume.py``` https://github.com/owenkim/pagerduty-alert-volume

A quick command-line to get the incident volume assigned to an escalation policy broken down by week.

## Incidents ##

### Get Incident Details

```get_incident_details_csv.py``` https://gist.github.com/danquixote/187fb09f64de3d294eda

Given a valid date-range, output incident-details to CSV in the format:  IncidentID,Created-At,Type,Agent/User,NotificationType,ChannelType,Summary

```pd-daily-incidents.py``` https://gist.github.com/julianeon/8327716

All the incidents in the given time range; here, one day.

```pd-service-incidents-print-file.rb``` https://gist.github.com/julianeon/7922342

A Ruby script to pull all the incidents from a service within a given time range and print the output to the file IncidentsInService.txt.

```Get Recent Incidents``` https://gist.github.com/ryanhoskin/7777921

Get incidents from PagerDuty that have been queued up for several days.

### Trigger Incidents ###

```pd-trigger-in-multiple-services.py``` https://gist.github.com/julianeon/7830174

Trigger incidents in multiple PagerDuty services.

## Incident Log Entries ##

```get_incident_log_entries.py``` https://gist.github.com/danquixote/8fa9a7f5d9d3b30be431

Given a valid date-range, get the ILE 'lifecycle' for the following log-entry types: Trigger, Assign, Escalate, Notify, Repeat\_Escalation\_Path, Acknowledge, Unacknowledge, Resolve, Annotate. Output will be in CSV in the format:  IncidentID,Created-At,Type,Agent/User,NotificationType,ChannelType,Notes

```pd-log-entry-detail.rb``` https://gist.github.com/julianeon/8564187

This retrieves the in-depth information about a specific log entry (for example, the body of an email).

```pd-log-entries.rb``` https://gist.github.com/julianeon/8563939

Get a summary of all log entries for an incident.

```pd-log-entry-print-file.rb``` https://gist.github.com/julianeon/8365468

Get the information about a specified log entry.

```pd-log-entries-with-timezone.rb``` https://gist.github.com/julianeon/7951622

This gets log entries in the appropriate time zone.

## Schedules ##

```pd-get-schedule.rb``` https://gist.github.com/julianeon/7915335

Ruby script to get an individual schedule.

### Create Vacation Overrides ###

```create_vacation_overrides.py``` https://gist.github.com/danquixote/4ca69fafac89bdb24080

Given a user going on vacation, create overrides for another user, only using the times the vacationing user is on-call.

## Users ##

### Get User Activity ###

```get_user_activity.py``` https://gist.github.com/ryanhoskin/8048001

Get the latest activity for all users within a PagerDuty account.

### Import Users from CSV ###

```process_users.py``` https://gist.github.com/danquixote/1de25bfd12ec27fa36ac

Given a CSV-file called 'users.csv', in the format:

```
name,email,role,address,type
Joe User,ju@example.com,user,15555555555,phone
Bob Dobbs,bd@example.com,admin,15555555554,sms
```

Create each user, a default contact-method/immediate email notification-rule, as well as an additional immediate notification-rule.

