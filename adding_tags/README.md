# Adding Tags for Users from CSV

## Input Format

To use this script, you must first have a CSV file ready formatted with the following headings:

```
email,tags
```

In this format:

- `email` is the user's login address, and it must uniquely match the user.
- `tags` a list of tag(s) you want to add to the user. The tag(s) MUST be in double quotes and comma separated e.g. "tag1,tag2,tag3"
- there must be **no spaces** between the commas and the items they separate  

## Input Format

To execute the script, run:

```
ruby add_user_tags.rb -a API_KEY_HERE -f PATH_TO_FILE_HERE
```

## Options

- `-a`/`--access-token`: _(required)_ REST API key (must be a global key)
- `-f`/`--csv-path`: _(required)_ path to the CSV file

## Errors

Errors are printed to the terminal as they happen, and are also recorded in a log file named after the requester_email. The log file will tell you the HTTP status, the response body, and the attempted payload or query.

#### The script performs API key's subdomain validation

The script will validate the initially provided API key and prompt to confirm by entering y/n. It will not start or exit until either option is selected.
