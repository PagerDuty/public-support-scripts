# Adding custom fields for incidents

## Input Format

To use this script, you must first have a CSV file ready formatted with the following headings:

```
data_type,name,display_name,description,field_type,field_options
```

In this format:

- `data_type` Allowed values: boolean, integer, float, string, datetime, url
- `name` The name of the field. May include ASCII characters, specifically lowercase letters, digits. The name field will be converted into a snake case. The name for a Field must be unique.
- `display_name` The human-readable name of the field. This must be unique across an account.
- `description` A description of the data this field contains.
- `field_type` The type of data this field contains. In combination with the data_type field.
Allowed values: single_value, single_value_fixed, multi_value, multi_value_fixed
- `field_options` The fixed list of value options that may be stored in this field.

## Input Format

To execute the script, run:

```
ruby import_custom_fields.rb -k API_KEY_HERE -f PATH_TO_CSV_FILE_HERE
```

## Options

- `-k`/`--api-key`: _(required)_ REST API key (must be a global key)
- `-f`/`--file-path`: _(required)_ path to the CSV file

## Errors

Errors are printed to the terminal as they happen, and are also recorded in a log file named after the requester_email. The log file will tell you the HTTP status, the response body, and the attempted payload or query.
