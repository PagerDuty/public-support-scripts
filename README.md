# PagerDuty Public Support Scripts

This is a collection of miscellaneous scripts that the PagerDuty Support Team
has written and collected over time. Their purpose is to perform specific,
limited-scope tasks through the REST API that cannot (as of the time that they
are written) be performed through the PagerDuty UI.

This README shall serve as both a set of instructions on the usage of these
scripts as well as a description of how this repository is to be maintained and
organized.

## Howto

Each of the directories within this repository describes a task in `snake_case`
carried out by the script(s).

In each of these directories shall be the script(s) that carry out the task, plus
documentation on usage.

Each script can be run as a standalone program, i.e.:
```
./name-of-script.lang <options>
``` 

As opposed to requring it to be run as follows, although it is also an option:

```
<interpreter> name-of-script.lang <options>
```

If including the command line flag `-h`, the script shall print out
instructions for usage ("helptext").

The directory shall also contain a file `README.md` containing any additional
usage instructions that cannot be included in the helptext and/or historical
information about the origin of the script (i.e. original author/source) and
how it has been used / can be used.

## Installing Dependencies

In some cases, scripts will require additional software modules or libraries in
order to run.

### Python Scripts

If the script is written in Python, the directory shall include a file
`requirements.txt`, which can be used to install dependencies with `pip` as
follows:

```
pip install -r ./requirements.txt
```

The program [pip](https://pip.pypa.io/en/stable/installing/) must be installed
in the local operating system in order to perform this type of dependency
installation.

More information on requirements files can be found in the pip documentation, at
[pip.pypa.io](https://pip.pypa.io/en/stable/user_guide/#requirements-files).

### Ruby Scripts

If the script is written in Ruby, the directory shall include a file `Gemfile`
specifiying gem dependencies, that can be used to install them using the
`bundle` command.

[Rubygems](https://rubygems.org/pages/download) will need to installed in the
local operating system in order to perform this type of dependency
installation.

More information on gemfiles and Bundle can be found here:
[bundler.io/gemfile.html](https://bundler.io/gemfile.html)

## Contributing

In addition to following each of the above conventions, i.e. residing in its
own directory, each script shall begin with with a "shebang" line as follows:

```
#!/usr/bin/env <interpreter>
```

Where `<interpreter>` is the language command (i.e. `ruby`, `python`, `perl`
etc.). Specific versions of interpreters (i.e. Python 2.7 or Python 3) shall be
specified in the name of the exectuable. If the generic name is used (i.e.
`python`), the script should be written such that it is compatible with the
widest possible range of versions that might be available on any given
operating system.

## External Scripts

The following is a list of supplemental scripts that may eventually be merged
into this collection and standardized/documented in the future according to the
outlined above. Any that remain referenced here indefinitely have been deemed
sufficiently well-documented and self-contained, i.e.:

- They reside in their own GitHub repository (which facilitates contributing to
  them) versus a Gist or a file in itself passed around
- They already follow many of the conventions of this collection of scripts
- The original maintainer is willing to review and accept pull requests to fix
  bugs
- They are both hosted and used externally / in the cloud, i.e. JSFiddle

### Alerts

#### Download Alerts to CSV

```
get_alerts_csv.py
```
https://gist.github.com/lfepp/69a2288d898248800752d38e593323c1

A sample script to programatically access and download the alerts for an
incident as a CSV file.

#### Alert Volume/Pain for On-Call Users

```
alert_volume.py
```
https://github.com/lfepp/pagerduty-alert-volume-v2

A quick command-line to get the incident volume assigned to an escalation policy broken down by week.

### Incidents

#### Get Incident Details

```
get_incident_details_csv.py
```
https://gist.github.com/lfepp/3678c96548a2bbc7707b5a781f17fdb0

Sample script to output incident details to a CSV in the format:

```
incident_id,created_at,type,user_or_agent_id,user_or_agent_summary,notification_type,channel_type,summary
```

#### Export Incidents to CSV

```
get_incidents_csv.py
```
https://gist.github.com/lfepp/89c960ca0f3dc1ab8e5569de9882fa90

Output all PagerDuty incidents for a given time period to a CSV file.

```
get_recent_incidents.sh
```
https://gist.github.com/lfepp/19cdc3ca469b4d353308c84a32853fe4

Sample shell script to pull PagerDuty incidents that were triggered within the given time period and are currently open.

#### Show All Incidents for a Service and Output to a File

```
incidents_in_service.rb
```
https://gist.github.com/lfepp/8cb74ae2a779b1088b5a69127d4f6e61

Pull all the incidents from a service within a given time range and print the output to the file `incidents_in_service.txt`

#### Incidents Functions

```
trigger_incident_multiple_services.py
```
https://gist.github.com/lfepp/a6441d1c5be7f30257a0cf0206c924c6

Trigger an incident within multiple PagerDuty services.

#### Manage Incidents

```
incidents.py
```
https://github.com/ryanhoskin/pagerduty_incident_functions

Trigger/acknowledge/resolve PagerDuty incidents

#### Snooze a PagerDuty incident

http://jsfiddle.net/jorts/dckwt4nu/

JSFiddle to snooze an incident within your account

### Incident Log Entries

#### Get Log Entry Details

```
get_log_entry_details.rb
```
https://gist.github.com/lfepp/76efb994c8460e5940f1ef8d26a36964

Script to retrieve detailed information about a specific log entry

```
get_log_entry_details_file.rb
```

https://gist.github.com/lfepp/6ccf3369e34bf5bc50a63578c103b807

Script to retrieve detailed information about a specific PagerDuty log entry in a plain text file

#### Retrieve Lists of Log Entries

```
get_incident_log_entries.rb
``` 
https://gist.github.com/lfepp/698f87fbb7dec5872276be058e05804a

Get a summary of all log entries for an incident

### Schedules

#### Get Details of a Schedule
```
get_schedule.rb
```
https://gist.github.com/lfepp/280893d1a1007f871022a0c6a5f77dc1

Retrieve information about a specific schedule

#### List Schedules by Name

http://jsfiddle.net/jorts/yrm1qbg4/

JSFiddle to list all PagerDuty schedules by name

#### List On-Call Shifts for a PagerDuty Schedule

http://jsfiddle.net/jorts/wmnfkg0L/

JSFiddle to list on-call shifts for a particular schedule

### Services

#### Update Settings on All PagerDuty Services

http://jsfiddle.net/jorts/e6y93y6r/

JSFiddle to update acknowledgement_timeout and auto_resolve_timeout parameters on all PagerDuty services

#### Schedule Recurring Maintenance Windows

```
recurring_maintenance_windows.py
```
https://gist.github.com/lfepp/32afebc59aa4b88a733bcc1b4f7236f9

Schedule a recurring regular maintenance window for a service or services.

### Remove All Future Maintenance Windows

```
remove_future_maintenance_windows.py
```
https://gist.github.com/lfepp/047a363d504d6aa3945f42a4b6d08886

Removes all future maintenance windows for a service or from your entire account.

## Users

#### Get User Activity

```
get_user_activity.py
```
https://gist.github.com/lfepp/c77421fb909f2a03114585cd19d35ad8

Get the latest activity for all users within a PagerDuty account.

#### List PagerDuty Users who Don't Have a Minute 0 Phone Notification

http://jsfiddle.net/jorts/vLhdL7ew/

#### List users who have a small # of Notification Rules

http://jsfiddle.net/jorts/5uw7bdkw/

#### List On-Call Users

http://jsfiddle.net/jorts/uvgv57kw/

Also: same as above, but with

https://github.com/ryanhoskin/pagerduty_oncall_dashboard

#### Import Users from CSV

```
create_users.py
```
https://gist.github.com/lfepp/7180035950984ed5937ceec6f2566c92

Given a CSV named "users.csv" in the format:

```
name,email,role,address,type
John Doe,john.doe@example.com,admin,5555555555,phone
Jane Doe,jane.doe@example.com,user,5555555554,sms
```

Creates each user, creates a default contact method and immediate notification rule for email, and creates a contact method and immediate notification rule for SMS or phone.

**Note:** Phone address must be a valide 10-digit phone number
**Note:** Address type must be one of ```sms``` or ```phone```

#### Import Users from Active Directory

If you are looking for an integration with ADFS, use this guide:

https://www.pagerduty.com/docs/guides/setup-adfs-sso-pagerduty/

If you would like a one-time import of users via AD, you can use this:

```
import_users_from_ad.ps1
```
https://gist.github.com/lfepp/ec388dbeb2c2ad301313143f44844fa5

#### List PagerDuty Users with Contact Information

http://jsfiddle.net/jorts/ve1sbyfw/

### Webhooks

#### Add webhooks to every PagerDuty service

http://jsfiddle.net/jorts/2n6a0rvv/

#### Replace Webhook URL on All PagerDuty Services

http://jsfiddle.net/jorts/yssbpupm/

## License and Copyright

Copyright (c) 2016, PagerDuty
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of [project] nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
