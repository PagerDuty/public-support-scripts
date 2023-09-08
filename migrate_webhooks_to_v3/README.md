# Migrate webhooks to V3

The `migrate_webhooks_to_v3.py` script will allow you to 
create a v3 version of your existing v1 and v2 generic webhooks. 
A JSON file will be created by the script to back up the information about the webhooks.

Since v3 webhooks have new [types of events](https://support.pagerduty.com/docs/webhooks#supported-resources-and-event-types) 
compared to older versions, the script's `-e` (`--event-types`) parameter  allows you to only send events for those types present in v1/v2 or for all types of events,m
including the newly added ones. You can choose to delete the old versions of the webhooks or keep them
(this is controlled by `-a` or `--action` parameter). 

Note that webhooks' custom headers will not be migrated.

### Usage

To migrate generic v1/v2 webhooks to v3:

1. Migrate v1 webhooks: `migrate_webhooks_to_v3.py -k {API-KEY} -v v1` OR migrate v1 and v2 webhooks: `migrate_webhooks_to_v3.py -v all -k {API-KEY}`
2. Confirm the migration was successful via the UI or REST API
3. Delete the v1 webhooks: `migrate_webhooks_to_v3.py -k {API-KEY} -v v1 -a delete` OR delete the v1 and v2 webhooks: `migrate_webhooks_to_v3.py -k {API-KEY} -v all -a delete`
