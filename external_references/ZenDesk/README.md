# PagerDuty to ZenDesk Incident Mapping
The `pagerduty_zendesk_incidents.py` script sends a GET request to the incidents endpoint to retrieve incident data, filters for incidents containing ZenDesk metadata, and then generates a CSV file mapping the PagerDuty incidents to their corresponding ZenDesk tickets:

- PagerDuty Incident Number
- Title
- Description
- Created At
- Updated At
- Status
- PagerDuty Incident URL
- ZenDesk Ticket ID
- ZenDesk Ticket URL

## Requirements

- Python 3.6+
- PagerDuty API Access Token

## Installation

1. Clone this repository
   ```bash
   git clone https://github.com/shirleyilenechan/incident_mappings.git
   ```
2. `cd` to the ZenDesk directory within `external_references`.

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a `.env` file in the ZenDesk directory.

2. Update the `.env` file with your PagerDuty API key:
   ```
   PAGERDUTY_REST_API_KEY=your_api_key_here
   ```

3. Define your request parameters in the `request_parameters.py` file.

4. Run the `pagerduty_zendesk_incidents.py` script in the ZenDesk directory:
   ```bash
   python3 pagerduty_zendesk_incidents.py
   ```

## How the Script Works

The `pagerduty_zendesk_incidents.py` script will:

1. Send a GET request to the incidents endpoint to retrieve incident data
2. Filter incidents to include only those with ZenDesk references
3. Generate a CSV file named `pagerduty_incidents_mapped_to_zendesk.csv` in the ZenDesk directory.

## Error Handling

The `pagerduty_zendesk_incidents.py` script will exit with an error message in the following cases:

- If the PagerDuty API request fails
- If no incidents with ZenDesk metadata are found

## Security Notes

1. Never commit your `.env` file
2. User Token Rest API Keys are restricted in accordance with the user's access and permissions, so the GET request to the incidents endpoint will only retrieve incidents that the user has access to. General Access Rest API Keys do not have such restrictions.

## Resources

1. [List incidents endpoint documentation](https://developer.pagerduty.com/api-reference/9d0b4b12e36f9-list-incidents)
2. [Pagination documentation](https://developer.pagerduty.com/docs/pagination)
3. [API Access Keys documentation](https://support.pagerduty.com/main/docs/api-access-keys)