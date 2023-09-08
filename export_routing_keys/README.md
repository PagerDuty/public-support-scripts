# Export Routing Keys

The scripts in this folder provide a method to inspect routing keys on an account.

## Get All Routing Keys in Account - `export_routing_keys.py`

This script generates a CSV report of all routing keys on the account across Service Integrations, Event Orchestrations, and Event Rulesets. 

### Input Format

Running the script requires the provision of only one required argument: a global REST API key

To execute the script, run this with your key:

```
./export_routing_keys.py -k API_KEY_HERE -o CSV_FILE_PATH
```

### Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)
- `-o`/`--csv-file`: _(optional)_ File path to write results in CSV format. (Default: standard output)

### Output Format

This script will generate a results in CSV format with the following columns:
- `Integration Type`: Indicates if the routing key belongs to a Service Integration, Event Orchestration, or Event Ruleset.
- `Routing Key`: The routing/integration key.
- `Name`: The user defined name for the key. 
- `Link`: Link to the resource in PagerDuty.

