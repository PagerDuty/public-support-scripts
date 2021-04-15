# Enable All Extensions

Extensions can become temporarily disabled if their webhooks are not successfully received.  More information on those circumstances in our documentation:  https://developer.pagerduty.com/docs/webhooks/webhook-behavior/

While these disabled extensions will automatically be reenabled after 24 hours, it may be useful at times to be able to enable all extensions intentionally at a chosen time without waiting for the 24-hour automation to restore extension functionality, such as when returning to normal functionality after coming out of maintenance.  

This python script will enable all temporarily disabled extensions on an account.  


## Input Format

Running the script requires the provision of only two arguments: a global REST API key and the email address of the user executing the script.

To execute the script, run this with your key and email:

```
python3 enable_all_extensions.py -k API_KEY_HERE -e REQUESTER_EMAIL
```

## Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)
- `-e`/`--requester-email`: _(required)_ Requester email address


