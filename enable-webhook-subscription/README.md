# Activate Webhook Subscriptions (Generic Webhooks v3)

Generic webhook v3 subscriptions can either be active or inactive. This script checks for all inactive webhook subscriptions in your PagerDuty account.
If any inactive webhooks are found, they will be displayed in the terminal, and you will be prompted to enable them.
Additionally, a CSV file containing all inactive webhooks will be downloaded for your reference.

## How to Run the Script

There are two methods to enable the webhooks using this script.
- **Method 1**: Run the script to detect and enable inactive webhooks.
- **Method 2**: Use a pre-existing CSV file of inactive webhooks to enable them directly.

### Method 1: Enable Webhooks Automatically

Run the following command in your terminal:

```bash
ruby webhook_subscription.rb -a {api-token}
```

### Method 2: Enable Webhooks Using a CSV File

If you already have a CSV file containing inactive webhook IDs, you can supply its path and use an additional option to enable them.
Run the following command in your terminal:

```bash
ruby webhook_subscription.rb -a {api-token-here} -f {path/to/csv file} -e activate_wsub
```

This command reads the webhook IDs from the CSV file and activates the corresponding webhook subscriptions.

### Notes

Ensure you have Ruby installed on your machine to run the script.
The script requires an active API token with the necessary permissions to manage webhooks in PagerDuty.
Use Method 2 if you already have a CSV file of inactive webhook IDs to save time.
