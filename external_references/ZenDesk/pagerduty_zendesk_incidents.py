import requests
import json
import csv
import os

from dotenv import load_dotenv

import request_parameters as parameters

load_dotenv()
PAGERDUTY_REST_API_KEY = os.getenv("PAGERDUTY_REST_API_KEY")


def get_incidents():
    """
    Makes a GET request to the incidents endpoint to retrieve incident data.
    
    Raises:
        SystemExit: If the API request fails or returns an error.
        
    Returns:
        dict: JSON response containing incident data if successful.
    """
    url = "https://api.pagerduty.com/incidents"

    querystring = {"include[]":"metadata"}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token token={PAGERDUTY_REST_API_KEY}"
    }

    if parameters.since:
        querystring["since"] = parameters.since
    if parameters.until:
        querystring["until"] = parameters.until
    if parameters.limit:
        querystring["limit"] = parameters.limit
    if parameters.offset:
        querystring["offset"] = parameters.offset

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        if response.text:
            return response.json()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    

def filter_incidents(incidents):
    """
    Filter incidents to only include those with ZenDesk metadata.
    
    Iterates through the incidents and keeps only those containing
    ZenDesk metadata.
    
    Args:
        incidents (dict): JSON dict containing incident data returned from the GET request
        to the incidents endpoint.
        
    Raises:
        SystemExit: If no incidents with ZenDesk metadata are found.
        
    Returns:
        list: incidents containing ZenDesk metadata.
    """
    incidents_with_metadata = []
    for incident in incidents["incidents"]:
        if incident["metadata"] != []:
            #only include incidents with servicenow metadata
            if any("zendesk" in key.lower() for key in incident["metadata"]):
                incidents_with_metadata.append(incident)

    if not incidents_with_metadata:
        raise SystemExit("No ZenDesk metadata found in any incidents")
    
    return incidents_with_metadata


def generate_csv(filtered_incidents):
    """
    Generate a CSV file mapping PagerDuty incidents to ZenDesk data.
    
    Creates a CSV file with relevant PagerDuty incident information (PagerDuty Incident Number", "Title", "Description", 
    "Created At", "Updated At", "Status", "PagerDuty Incident URL") and
    the corresponding ZenDesk ticket IDs and ticket URLs.
    
    Args:
        filtered_incidents (list): List of incidents containing ZenDesk metadata.
    """
    csv_filename = "pagerduty_incidents_mapped_to_zendesk.csv"
    # Define the header for the CSV
    headers = ["PagerDuty Incident Number", "Title", "Description", "Created At", "Updated At", "Status", "PagerDuty Incident URL", "ZenDesk Ticket ID", "ZenDesk Ticket URL"]
    # Write to CSV file
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for incident in filtered_incidents:
            for key, value in incident["metadata"].items():
                if "zendesk" in key:
                    zendesk_key = key
                    zendesk_value = json.loads(value)
                    external_name = zendesk_value.get("external_name", "")
                    external_url = zendesk_value.get("external_url", "")
                    writer.writerow({
                        "PagerDuty Incident Number": incident.get("incident_number", ""),
                        "Title": incident.get("title", ""),
                        "Description": incident.get("description", ""),
                        "Created At": incident.get("created_at", ""),
                        "Updated At": incident.get("updated_at", ""),
                        "Status": incident.get("status", ""),
                        "PagerDuty Incident URL": incident.get("html_url", ""),
                        "ZenDesk Ticket ID": external_name,
                        "ZenDesk Ticket URL": external_url
                    })

def main():
    incidents = get_incidents()
    filtered_incidents = filter_incidents(incidents)
    csv = generate_csv(filtered_incidents)


if __name__ == "__main__":
    main()