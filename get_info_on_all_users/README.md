# Get Info On All Users

The scripts in this folder provide a variety of methods to pull information on all users in a PagerDuty account.

## Get All Users' Contact Methods - `contact_methods.py`

This script retrieves contact info for all users in a PagerDuty account and outputs it in the console in an easy to read format.

### Input Format

Running the script requires the provision of only one argument: a global REST API key

To execute the script, run this with your key:

```
./contact_methods.py -k API_KEY_HERE
```

### Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)

## Get All Users With Certain Roles - `get_users_by_role.py`

This script will take a comma separated list of roles as a command line argument and fetches all the users in an account that match one of roles provided in the list. Roles will be fetched in the order that they are provided in the command line argument. Running with -v flag will show which role is being retrieved and then list the members who match it. After retrieving all the members for a given role, a tally will be shown for how many users have that role.

The script also creates a csv with names in the first column and users in the second. At the bottom of the CSV the totals for each role type are listed.

### Input Format

Running the script requires the provision of three arguments: a global REST API key, a list of roles, and a filename for the csv output. See the "Options" section below for details.

To execute the script, run this with your key:

```
./get_users_by_role.py -k API-KEY-HERE -r COMMA-SEPARATED-ROLES-LIST -f FILENAME-FOR-CSV
```

You can also optionally turn on verbose logging in the console with the `-v` option.

### Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)
- `-r`/`--roles`: _(required)_ A comma-separated list of roles to be fetched
    - Acceptable values for roles: `admin,read_only_user,read_only_limited_user,user,limited_user,observer,restricted_access,owner,team_managers`
- `-f`/`--filename`: _(required)_ The filename to use for the output csv. If the argument entered doesn't end in `.csv`, then `.csv` will be appended.
- `-v`/`--logging`: _(optional)_ Turn on verbose logging in the console

## Get Team Roles of All Users - `team_roles.py`

This script will retrieves team roles for all users in a PagerDuty account that are members of any team. The default output is by user in the console, however you can optionally have the console output in comma-separated format for easier processing by using the `-c` option.

### Input Format

Running the script requires the provision of just one argument: a global REST API key

To execute the script, run this with your key:

```
./team_roles.py -k API-KEY-HERE
```

You can also optionally turn on comma-separated formatting in the console with the `-c` option.

### Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)
- `-c`/`--comma-separated`: _(optional)_ Format console output separated by commas

## Get User Role Changes

This script retrieves user role changes for all users in a PagerDuty account. By default the script will output
a text formatted table to the console for user role changes in the past 24 hours. The script can optionally be configured to get role tier changes, can filter by a particular user ID, can filter by different date ranges,
and can write results to a CSV file.

The following fields are returned by the script:
- Date: ISO datetime string when the role change occurred
- User ID: User ID of the user that the role change occurred on
- User Name (not required): The user's nane that the role change occurred on
- Role/Tier Before: The role/tier of the user before the change occurred
- Role/Tier After: The role/tier of the user after the change occurred
- Actor ID: The ID of the most specific actor that made the role change
- Actor Type: The type of the most specific actor that made the role change
- Actor Summary (not required): The display name of the most specific actor that made the role change

### Usage

Running the script requires one argument: a global REST API key

```
./get_user_role_changes.py -k API-KEY-HERE
```

#### Custom Date Range

```
./get_user_role_changes.py -k API-KEY-HERE --since 2023-05-08T05:15:00Z --until 2024-05-08T05:15:00Z
```

#### Filter by User ID

```
./get_user_role_changes.py -k API-KEY-HERE --user-id PABC123
```

#### Exclude user create and deletes

By default when a user is create this script will include role changes from user creates and deletes,
(None -> New Role, Old Role -> None). To exlucde these from reported results use the `--only-updates`
options.

```
./get_user_role_changes.py -k API-KEY-HERE --only-updates
```

#### Role Tier Changes

Instead of getting all role changes, get all role tier changes in table format.

```
./get_user_role_changes.py -k API-KEY-HERE --tier-changes
```

#### Write Results to CSV

```
./get_user_role_changes.py -k API-KEY-HERE --filename user_role_changes.csv
```

#### Show all user change audit records

In some cases you may want to see all user changes or the complete role change audit record.
This option provides a basic implementation to print the records in JSON format.

```
./get_user_role_changes.py -k API-KEY-HERE --show-all
```

### Options

To view all of the options available run the script with the help flag:

```
./get_user_role_changes.py --help

  -k API_KEY, --api-key API_KEY       REST API key
  -s SINCE, --since SINCE             Start of date range to search
  -u UNTIL, --until UNTIL             End of date range to search
  -i USER_ID, --user-id USER_ID       Filter results to a single user ID
  -o, --only-updates                  Exclude user creates and deletes from role change results
  -t, --tier-changes                  Get user role tier changes
  -a, --show-all                      Prints all fetched user records in JSON format
  -f FILENAME, --filename FILENAME    Write results to a CSV file
```
