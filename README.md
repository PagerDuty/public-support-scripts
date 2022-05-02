# PagerDuty Public Support Scripts

This is a collection of miscellaneous scripts that the PagerDuty Support Team
has written and collected over time. Their purpose is to perform specific,
limited-scope tasks through the REST API that cannot (as of the time that they
are written) be performed through the PagerDuty UI.

This README shall serve as both a set of instructions on the usage of these
scripts and a description of how this repository is to be maintained and
organized.

## Contents

* [Enable all extensions](enable_all_extensions): enable all disabled extensions.
* [Get info on all users](get_info_on_all_users): get various information on users 
  in your account.
* [Import users](import_users): add users to your PagerDuty account from a CSV file.
* [Maintenance window bulk operations](maintenance_windows_bulk_operations):
  schedule series of recurring maintenance windows, and bulk-delete future
  maintenance windows.
* [Mass update incidents](mass_update_incidents): update or resolve many
  incidents in an automated fashion
* [Migrate webhooks to v3](migrate_webhooks_to_v3): migrate all your v1/v2 extensions 
  to v3.
* [Notifications team report](notifications_team_report): generate a report of
  notification counts scoped to one or more specific teams
* [Overrides bulk operations](overrides_bulk_operations): schedule vacation
  overrides for a given user, list overrides, or mass-delete a list of
  overrides.
* [Remove SMS contact methods](remove_sms_contact_methods): delete SMS-type
  contact methods and notification rules for all users in a PagerDuty account
* [Rerole users](rerole_users): give users new roles.
* [Schedule layer reorganizer](schedule_layer_reorganizer): transform response of 
  GET request to /schedules endpoint to format required for subsequent PUT/POST requests.
* [Update user emails](update_user_emails): perform account-wide modifications
  to login email addresses of users based on search and replace patterns,
  including with regular expressions
* [De-provision users](user_deprovision): automate the off-boarding process for
  PagerDuty users by removing them from schedules and escalation policies, and
  resolving all incidents that they are assigned.

## Howto

Each of the directories within this repository describes a task in `snake_case`
carried out by the script(s).

In each of these directories shall be the script(s) that carry out the task, plus
documentation on usage.

Each script can be run as a standalone program, i.e.:
```
./name-of-script.lang <options>
``` 

As opposed to requiring it to be run as follows, although it is also an option:

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
specifying gem dependencies that can be used to install them using the
`bundle` command.

[Rubygems](https://rubygems.org/pages/download) will need to installed in the
local operating system in order to perform this type of dependency
installation.

More information on gemfiles and Bundle can be found here:
[bundler.io/gemfile.html](https://bundler.io/gemfile.html)

## Contributing

In addition to following each of the above conventions, i.e. residing in its
own directory, each script shall begin with a "shebang" line as follows:

```
#!/usr/bin/env <interpreter>
```

where `<interpreter>` is the language command (i.e. `ruby`, `python`, `perl`
etc.). Specific versions of interpreters (i.e. Python 2.7 or Python 3) shall be
specified in the name of the executable. If the generic name is used (i.e.
`python`), the script should be written such that it is compatible with the
widest possible range of versions that might be available on any given
operating system.

## License and Copyright

Copyright (c) 2016, PagerDuty
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of [project] nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
