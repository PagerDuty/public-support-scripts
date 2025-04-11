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

    querystring = {"include[]":"external_references"}

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
    Filter incidents to only include those with Jira external_reference.
    
    Iterates through the incidents and keeps only those containing
    Jira external_reference.
    
    Args:
        incidents (dict): JSON dict containing incident data returned from the GET request
        to the incidents endpoint.
        
    Raises:
        SystemExit: If no incidents with Jira external_reference are found.
        
    Returns:
        list: incidents containing Jira external_reference.
    """
    incidents_with_jira_reference = []
    for incident in incidents["incidents"]:
        if incident["external_references"] != []:
            for reference in incident["external_references"]:
                if "JIRA" in reference["summary"]:
                    incidents_with_jira_reference.append(incident)
    
    if not incidents_with_jira_reference:
        raise SystemExit("No Jira external_reference found in any incidents")
    
    return incidents_with_jira_reference
    
def generate_csv(filtered_incidents):
    """
    Generate a CSV file mapping PagerDuty incidents to Jira data.
    
    Creates a CSV file with relevant PagerDuty incident information (PagerDuty Incident Number", "Title", "Description", 
    "Created At", "Updated At", "Status", "PagerDuty Incident URL") and
    the corresponding Jira ticket IDs and Jira ticket URLs.
    
    Args:
        filtered_incidents (list): List of incidents containing Jira external_reference.
    """
    csv_filename = "pagerduty_incidents_mapped_to_jira.csv"
    # Define the header for the CSV
    headers = ["PagerDuty Incident Number", "Title", "Description", "Created At", "Updated At", "Status", "PagerDuty Incident URL", "Jira Ticket ID", "Jira Ticket URL"]
    # Write to CSV file
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for incident in filtered_incidents:
            for reference in incident["external_references"]:
                writer.writerow({
                    "PagerDuty Incident Number": incident.get("incident_number", ""),
                    "Title": incident.get("title", ""),
                    "Description": incident.get("description", ""),
                    "Created At": incident.get("created_at", ""),
                    "Updated At": incident.get("updated_at", ""),
                    "Status": incident.get("status", ""),
                    "PagerDuty Incident URL": incident.get("html_url", ""),
                    "Jira Ticket ID": reference["external_id"],
                    "Jira Ticket URL": reference["external_url"],
                })


def main():
    incidents = get_incidents()
    filtered_incidents = filter_incidents(incidents)
    csv = generate_csv(filtered_incidents)


if __name__ == "__main__":
    main()