# Rerole Script

Give users new roles.

New roles can be assigned on one of the following bases:

* **Account-wide:** give all users a specific base role/team role
* **Per-user:** give each user listed in a CSV file a specific base role and a role on all of their teams
* **Per-user per-team:** given a list of roles in a CSV file, each record specifying *user-X-has-role-Y-on-team-Z*, give each user the specific permission on that specific team.

In all cases, more granular / specific permissions take precedence over more general permissions, i.e. roles that are given on a per-user basis in a CSV will take precedence over roles specified via command line arguments. However, command line arguments can be combined with CSV input files to specify default roles to assign in addition to the roles specified in CSV files, in cases where they're unspecified in the input.

For instance, if specifying per-user roles in a CSV file and base role `observer` on the command line, all users in rows that have an empty second column will be granted a new base role of Observer, but any that have a non-empty second column that is `limited_user` will be given the base role of Responder.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Valid Role Values](#valid-role-values)
- [Input File Format](#input-file-format)
  - [Per-user Roles and Listing Users](#per-user-roles-and-listing-users)
  - [Per-user Per-team Roles](#per-user-per-team-roles)
- [Usage](#usage)
  - [Getting Started](#getting-started)
  - [Viewing Built-in Documentation](#viewing-built-in-documentation)
  - [Basic Usage](#basic-usage)
  - [Roles from a CSV File](#roles-from-a-csv-file)
  - [Roles From the Command Line](#roles-from-the-command-line)
  - [Setting Roles on a Per-Team Basis](#setting-roles-on-a-per-team-basis)
  - [Backing Up and Restoring User Role Data](#backing-up-and-restoring-user-role-data)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Valid Role Values

Whether in a CSV file or in a command line argument, **you will need to properly specify the role values according to the API documentation, or they will be ignored/skipped.**

* **When specifying a base role** (the default role that the user will have, barring any specific role on a given team), it should be one of the values as specified in our Knowledge Base under [Advanced Permissions: Roles in the REST API and SAML](https://support.pagerduty.com/v1/docs/advanced-permissions#section-roles-in-the-rest-api-and-saml), i.e. `limited_user` to specify a Responder. This list can also be found in the REST API documentation for [updating users](https://api-reference.pagerduty.com/#!/Users/put_users_id).
* **When specifying a team-level role,** it should be one of the values given in our API docs for the request schema of the action [Add a user to a team (`PUT /teams/{id}/users/{user_id}`)](https://api-reference.pagerduty.com/#!/Teams/put_teams_id_users_user_id), i.e.
  * `observer`: Observer
  * `responder`: Responder
  * `manager`: Manager

## Input File Format

The script can read input data from a CSV file. Note:

* **All CSV files must be in Unix/Mac compatible format, with Unix-style linebreaks.** To convert a CSV file from Windows format (i.e. created by Microsoft Excel CSV export) to Unix format, use the utility [dos2unix](https://linux.die.net/man/1/dos2unix), which can be installed via Homebrew by running `brew install dos2unix`.
* **CSV Files must not have a column headers row**, i.e. data must start on the first line of the file.

### Per-user Roles and Listing Users

Use the `-o/--roles-from-file` option with a CSV file name to use as input, i.e. `./rerole_users.py -o user-roles.csv`.

For roles specified per-user in the CSV file:

1. **First column**: the login email of the user (required)
2. **Second column:** the new base role to set for the user (optional); will default to the role specified in the command line options if not given in this column of the CSV file.
3. **Third column:** the role to set on all teams of which the user is a member (optional); will default to the team role as specified in the command line options if omitted.

E.G. for a user to have a base role of Responder and a role of Manager on all their teams, add the following row:

```
janedoe@example.com,limited_user,manager
```

**If you just want to include the user** in a re-roling where the new roles are specified at the command line (and not specify any per-user roles):

```
janedoe@example.com
```

**If you want to change the team role but not the base role,** i.e. make the user a manager on all their teams and not touch their base role, leave the second column blank, i.e.

```
janedoe@example.com,,manager
```

Alternately, **if you want to change the base role and leave team roles unchanged:** leave the third column blank or don't include it, i.e.

```
janedoe@example.com,observer,
```

### Per-user Per-team Roles

Use the `-t/--team-roles-from-file` option with a CSV file to use as input, i.e. `./rerole_users.py -t team-roles.csv`.

For team roles specified per-user and per-team in a CSV file:

1. **First column:** user login email
2. **Second column:** the team-level role to grant the user
3. **Third column:** the name of the team (must match EXACTLY) on which to grant the user the role.

Note, one can specify the same user and role multiple times in the file to grant them different roles on different teams, i.e.

```
janedoe@example.com,manager,Team A
janedoe@example.com,responder,Team B
janedoe@example.com,observer,Team C
```

## Usage

### Getting Started

First, download the script and its dependencies file `requirements.txt`.

Next, if you don't already have a Python virtual environment set up, make a new one ad-hoc:

```
virtualenv env
source env/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Make the script executable:

```
chmod +x rerole_users.py
```

### Viewing Built-in Documentation

To view help info text on how to run the script and available options, run it with the `-h` flag:

```
./rerole_users.py -h
```

### Basic Usage

The script requires the `-k/--api-key` option, to specify the REST API key to use for running the script, i.e. the following sets the base role of all users (except the owner and stakeholder users) to Observer:

```
./rerole_users.py --api-key API-KEY-HERE --all-users -r observer
```

Note, if you don't specify a CSV file for setting specific permissions, you must include the option `-a/--all-users` to rerole all users (otherwise, if you're not specifying users to rerole, what's to say who needs to be reroled?)

### Roles from a CSV File

Call the script with REST API key and path to CSV file as command line arguments.

```
./rerole_users.py --api-key API-KEY-HERE --roles-from-file user_roles.csv
```

### Roles From the Command Line

In addition to using a CSV file to specify which users should be re-roled, you can specify a single base role or team role for all users using the `-r/--new-role` and `-e/--team-role` options.. Note that the team role will be applied uniformly across all teams for the user.

If using `-a/--all-users`, it will re-role all users with the specified roles. Otherwise, if using `-o/--roles-from-file`, this is where the precedence rules come into play, i.e. if a user's base or team role is specified both in the file and at the command line, the role given in the command line will take precedence. 

**Example:** One can set the base role of all users given in a file to observer (if unspecified), or use the role in the file otherwise:

```
./rerole_users.py --api-key API-KEY-HERE --new-role observer --roles-from-file users.csv
```

In the above example, let's say there are the following two lines:

```
janedoe@example.com,
usermcuserson@exmaple.com,user
```

In this example:

* User `janedoe@example.com` will be given the base role of `observer` (Observer)
* User `usermcuserson@example.com` will be given a base role of `user` (Manager).

**Example 2:** Similarly, one can apply a team role uniformly to all specified users unless given in the CSV:

```
./rerole_users.py --api-key API-KEY-HERE --team-role responder --users-from-file users.csv
```

Let's say then that the `users.csv` file contains the following:

```
janedoe@example.com,limited_user,manager
usermcuserson@example.com,observer,
```

In this example:

* User `janedoe@example.com` will be given a base role of `limited_user` (Responder) and team role `manager` (Manager)
* User `usermcuserson@example.com` will be given a base role of `observer` (Observer) and a team role `responder` (Responder)

### Setting Roles on a Per-Team Basis

Call the script with the `-t/--team-roles-from-file` option, i.e.:

```
./rerole_users.py --api-key API-KEY-HERE --team-roles-from-file teamroles.csv
```

The format of `teamroles.csv` should be as described in [Input File Format: Per-user Per-team Roles](#per-user-per-team-roles)

### Backing Up and Restoring User Role Data

It is highly recommended that you include both the `-b/--rollback-file` and `-m/--rollback-teamroles-file` options when running the script. These will create files that can be used to restore the roles (both team roles and base roles) to what they were before running the reroler script.

With each of these options, you must include a filename, and then after the reroler finishes running, the reroler can be run again with the named files as input.

**Example:** let's say there was a mistake and we want to restore the team roles, reevaluate what they should be, and then set them accordingly. The operation will proceed as follows:

*1. Rerole:* set all users to base role observer by default, and otherwise set base roles and roles on all teams as specified in the CSV file:

```
./rerole_users.py --api-key API-KEY-HERE \
  -r observer --roles-from-file user_roles.csv \
  --rollback-file baseroles-backup.csv \
  --rollback-teamroles-file teamroles-backup.csv
```

*2. Whoops:* we set some team roles for all of a few users' teams, and they should actually have distinct roles for each. We restore as follows:

```
./rerole_users.py --api-key API-KEY-HERE \
  --team-roles-from-file teamroles-backup.csv
```

*3. Prepare to do it right this time:* Open the new csv file in a spreadsheet, change values as desired and then re-export to a different CSV file teamroles-new.csv, then re-run the script:

```
dos2unix teamroles-new.csv

./rerole_users.py --api-key API-KEY-HERE \
  --team-roles-from-file teamroles-new.csv
```

Note, the same can be done for base roles using (in the above example) the file `baseroles-backup.csv`, and setting the option `--roles-from-file baseroles-backup.csv` to restore base roles.
