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

### Incidents Functions ###

```pd-trigger-in-multiple-services.py``` https://gist.github.com/julianeon/7830174

Trigger incidents in multiple PagerDuty services.

```incidents.py``` https://github.com/ryanhoskin/pagerduty_incident_functions

Trigger/acknowledge/resolve PagerDuty incidents.

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

### Import Users from Active Directory ###

If you are looking for an integration with ADFS, use this guide:  https://www.pagerduty.com/docs/guides/setup-adfs-sso-pagerduty/

If you would like a one-time import of users via AD, you can use this:  https://gist.github.com/ryanhoskin/4544017

### List PagerDuty Users with Contact Information ###
http://jsfiddle.net/jorts/ve1sbyfw/

## Webhooks ##

###Replace Webhook URL on All PagerDuty Services ### 

http://jsfiddle.net/jorts/yssbpupm/

##License and Copyright
Copyright (c) 2014, PagerDuty
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of [project] nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
