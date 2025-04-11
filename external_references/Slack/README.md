# PagerDuty to Slack Incident Mapping
The `pagerduty_slack_incidents.py` script sends a GET request to the log_entries endpoint to retrieve log entries data, filters for log entries containing a Slack incident post, and then generates a CSV file mapping PagerDuty incidents to their corresponding Slack incident posts:

- PagerDuty Incident Title
- PagerDuty Incident URL
- Slack Channel Name
- Slack Incident Post URL

## Requirements

- Python 3.6+
- PagerDuty API Access Token

## Installation

1. Clone this repository
   ```bash
   git clone https://github.com/shirleyilenechan/incident_mappings.git
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a `.env` file in the Slack folder where you cloned the incident_mappings repository.

2. Update the `.env` file with your PagerDuty API key:
   ```
   PAGERDUTY_REST_API_KEY=your_api_key_here
   ```

3. Define your request parameters in the `request_parameters.py` file.

4. Run the `pagerduty_slack_incidents.py` script from the command line, in the Slack folder where you cloned the incident_mappings repository:
   ```bash
   pagerduty_slack_incidents.py
   ```

## How the Script Works

The `pagerduty_slack_incidents.py` script will:

1. Send a GET request to the log_entries endpoint to retrieve log entry data
2. Filter log entries to include only those with a Slack incident post
3. Generate a CSV file named `pagerduty_incidents_mapped_to_slack.csv` in the Slack folder where you cloned the incident_mappings repository.

## Error Handling

The `pagerduty_slack_incidents.py` script will exit with an error message in the following cases:

- If the PagerDuty API request fails
- If no log entries containing a Slack incident incident post

## Security Notes

1. Never commit your `.env` file
2. User Token Rest API Keys are restricted in accordance with the user's access and permissions, so the GET request to the incidents endpoint will only retrieve incidents that the user has access to. General Access Rest API Keys do not have such restrictions.

## Resources

1. [List log entries documentation](https://developer.pagerduty.com/api-reference/c661e065403b5-list-log-entries)
2. [Pagination documentation](https://developer.pagerduty.com/docs/pagination)
3. [API Access Keys documentation](https://support.pagerduty.com/main/docs/api-access-keys)