# Import Users from CSV

**Note: this script should be run using a global API key (and not a personal/user API key). If a personal API token is used, this user will be added to every created team**

## Input Format

To use this script, you must first have a CSV file ready formatted as follows:

```
name,email,role,title,country_code,phone_number,teams,team_roles
```

In this format:

- `country_code` is the phone country code, and `phone_number` is the number
  without country code
- `teams` is a semicolon-delimited list of teams to which the given user should
  be added
- `team_roles` is a semicolon-delimited list of team roles that will be applied to the give team(s) in the order defined.
- `email` is the user's login address, and it must uniquely match the user.
- `role` must be a valid user role value; see [Roles in the REST API and
  SAML](https://support.pagerduty.com/v1/docs/advanced-permissions#section-roles-in-the-rest-api-and-saml)
  in the PagerDuty Knowledge Base.
- there must be **no spaces** between the commas and the items they separate  
- do not include column headers

## Team Roles

When a user is added to or associated with a team for the first time, their default team role will be dependent on their base role. Users can be added to a team manually or automatically by being added to an escalation policy that is associated with a team. Read more about team role [here](https://support.pagerduty.com/docs/advanced-permissions#section-roles-in-the-rest-api-and-saml).

| Base Role           | Default Team Role When Added to a Team |
|---------------------|----------------------------------------|
| Observer**          | Observer                               |
| Stakeholder         | Observer                               |
| Restricted Access** | Observer                               |
| Responder**         | Responder                              |
| Manager**           | Manager                                |
| Global Admin        | Manager                                |

** Users with flexible base roles (Restricted Access, Observer, Responder, Manager) can have their default team roles changed to grant them more more or less permissions on a specific team.

- There are three team roles `manager`, `responder` and `observer`
- A user with base role `admin` will be applied a fixed team role of `manager`
- A user with base role `ready_only_user` and `ready_only_limited_user` will be applied a fixed team role of `observer`
- If no team roles are supplied the default team role will be added to the team(s) based on the user role
- The order of the team should match the order of the team roles

```
..team1;team2,manager;observer
```
In the above example team1 will be set as manager and team2 will be set as observer respectively

- To apply the same team role for all teams you can define one team role

```
team1;team2;team3,observer
```

In the above example all the teams will be set as observer team role

- If you want the last team to have the team role as manager

```
...,team1;team2;team3,;;manager
```

In the above example the first two team roles are blank therefore responder team role will be applied and the last team will be set as manager

## Input Format

To execute the script, run:

```
ruby import_users.rb -a API_KEY_HERE -f PATH_TO_FILE_HERE -e REQUESTER_EMAIL
```

## Options

- `-a`/`--access-token`: _(required)_ REST API key (must be a global key)
- `-f`/`--csv-path`: _(required)_ path to the CSV file
- `-e`/`--requester-email`: _(required)_ Requester email address
- `-n`/`--no-new-teams`: _(optional)_ Disable the default team-creation behavior; if this flag is included and a team listed in the CSV doesn't exist, the team will _not_ automatically be created

## Errors

Errors are printed to the terminal as they happen, and are also recorded in a log file named after the requester_email. The log file will tell you the HTTP status, the response body, and the attempted payload or query.

## Notes and Caveats
Use --help to view all commandline options.

**Whitespace is bad**. The only place where whitespace is permitted is within fields: between the first and last names and inside team names and job titles. There cannot be whitespace anywhere else in the CSV.

If you'd like to **skip fields**, you need to indicate the empty interstitial fields using commas. For example, if I want to skip title, country code, and phone number, yet add a team, a line in the CSV would look like this:
```
Alex Thompson,alex.t@example.com.invalid,,,,Best Team Ever
```

Trailing commas can be omitted however, e.g., the following will work perfectly:
```
Alex Thompson,alex.t@example.com.invalid
```

Team names cannot contain the following characters: '\\', '/', '&', '<', '>' or non-printable characters.

This script should be run using a **global API key** (and not a personal/user API key). If a personal API token is used, this user will be added to every newly created team.

#### Teams will be created if they do not exist
This behavior can be disabled by adding the `-n` option.

#### Each user will be sent an invitation email the moment that they are created

This is a latent feature of the REST API that cannot be disabled. However, it
is possible to stop invites from being sent by appending `.invalid` to the
email addresses when importing. Later on, the email addresses can be updated in
bulk using a different automation.

#### The script can also be used to modify users in bulk

If the users corresponding to the email addresses already exist in the account,
then they will be added to the teams specified in the last column of the input
CSV, and moreover, contact methods will be added to them. However, if they
already have contact methods matching the phone numbers, an error will be
raised and the script will proceed to the next user without continuing work on
that user (i.e. adding them to teams).

If only adding users to a team, one can leave the phone number and phone
country code columns blank.

#### The parser cannot gracefully handle unicode characters or Windows-style linebreaks

If the CSV was generated by Microsoft Word, you should check the file first to
see if it has only Windows-stylle line endings. If it does, the parser will
treat the whole file as if it were one line. If in doubt, use the
[dos2unix](http://dos2unix.sourceforge.net/) tool to convert the file.

Moreover, some difficulty has been observed using this script with input files
that contain unicode characters.
