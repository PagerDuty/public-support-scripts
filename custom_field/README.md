# Adding custom fields for incidents

Before running the script it is recommended that you read the PagerDuty doc about [custom fields](https://support.pagerduty.com/docs/custom-fields-on-incidents) and understand how they work.

## Input Format

To use this script, you must first have a CSV file ready formatted with the following headings:

```
data_type,name,display_name,description,field_type,field_options
```

In this format:

- `data_type` Allowed values: `boolean`, `integer`, `float`, `string`, `datetime`, `url`
- `name` The name of the field. May include ASCII characters, specifically lowercase letters, digits. The name field will be converted into a snake case. The name for a Field must be unique.
- `display_name` The human-readable name of the field. This must be unique across an account.
- `description` A description of the data this field contains.
- `field_type` The type of data this field contains. In combination with the data_type field.
Allowed values: `single_value`, `single_value_fixed`, `multi_value`, `multi_value_fixed`
- `field_options` The fixed list of value options that may be stored in this field.

The `field_options` values MUST be separated by semicolon `;` see CSV example below for multiple field options.

```
data_type,name,display_name,description,field_type,field_options
string,test cusomt field,test custom field,test,multi_value_fixed,option1;option2;option3
```

## Understanding the field types
- `single_value_fixed` = Single Select in the UI
- `multi_value_fixed` = Multiple Select in the UI
- `single_value` = Text (data type is string), Checkbox (data type is boolean), URL (data type is url), Datetime (data type is datetime), Decimal (data type is float), integer (data type is integer)
- `multi_value` = tag (data type is string)


## Running the script

1. Download the repo or save the files in a directory

2. Now, in your terminal, navigate to the directory containing the files.

3. Run the following command to install the required gems:

```
bundle install
```

This will install the specified gems and their dependencies.


To execute the script, run:

```
bundle exec ruby import_custom_fields.rb -k API_KEY_HERE -f PATH_TO_CSV_FILE_HERE
```

Using `bundle exec` ensures that the script uses the gem and versions specified in the Gemfile.

if you alreay have the specified gems installed you can simple run the script like shown below.

```
ruby import_custom_fields.rb -k API_KEY_HERE -f PATH_TO_CSV_FILE_HERE
```

## Options

- `-k`/`--api-key`: _(required)_ REST API key (must be a global key)
- `-f`/`--file-path`: _(required)_ path to the CSV file

## Errors

Errors are printed to the terminal as they happen, and are also recorded in a log file named after the requester_email. The log file will tell you the HTTP status, the response body, and the attempted payload or query.

## Reference

The script utilises the PagerDuty REST API for creating [custom fields](https://developer.pagerduty.com/api-reference/2131f556073c4-create-a-field) and [options for custom fields](https://developer.pagerduty.com/api-reference/4d93407098d46-create-a-field-option)
