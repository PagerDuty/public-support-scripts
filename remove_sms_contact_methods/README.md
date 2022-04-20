# Delete All SMS Contact Methods

This removes all SMS contact methods and notification rules from an account.

Requires an admin-level or account-level API key to have the proper permissions
for removal. Refer to the following [guide](https://support.pagerduty.com/docs/api-access-keys) on how to create an API KEY.

# How to run the script

The script accepts one argument of `-k` which is the API Key.

```
python3 remove_sms_contact_methods.py -k API-KEY
```
