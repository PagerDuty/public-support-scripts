import requests
import json
import csv
import os

from dotenv import load_dotenv

import request_parameters as parameters

load_dotenv()
PAGERDUTY_REST_API_KEY = os.getenv("PAGERDUTY_REST_API_KEY")


def get_log_entries():
    """
    Makes a GET request to the log_entries endpoint to retrieve incident log entries.
    
    Raises:
        SystemExit: If the API request fails or returns an error.
        
    Returns:
        dict: JSON response containing incident log entries if successful.
    """
    url = "https://api.pagerduty.com/log_entries"


    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token token={PAGERDUTY_REST_API_KEY}"
    }

    querystring = {}

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
    

def filter_log_entries(log_entries):
    """
    Filter log entries to only include those with Slack channel type.
    
    Iterates through the log entries and keeps only those containing
    with Slack channel type.
    
    Args:
        log_entries(dict): JSON dict containing log entries returned from the GET request
        to the log_entries endpoint.
        
    Raises:
        SystemExit: If no log entries with Slack channel type are found.
        
    Returns:
        list: log entries containing Slack channel type.
    """
    entries_with_slack_channel = []
    for entry in log_entries["log_entries"]:
        if entry["channel"].get("type"):
            channel_type =  entry["channel"].get("type")
            if channel_type == "slack":
                entries_with_slack_channel.append(entry)
    
    if not entries_with_slack_channel:
        raise SystemExit("No Slack incident posts found in any incidents")
    
    return entries_with_slack_channel
    
def generate_csv(filtered_entries):
    """
    Generate a CSV file mapping PagerDuty incidents to Slack incident posts.
    
    Creates a CSV file with relevant PagerDuty incident information (PagerDuty Incident Number", "Title", "Description", 
    "Created At", "Updated At", "Status", "PagerDuty Incident URL") and
    the corresponding Slack channel names and Slack incident post URLs.
    
    Args:
        filtered_entries(list): List of log entries containing Slack channel type.
    """
    csv_filename = "pagerduty_incidents_mapped_to_slack.csv"
    # Define the header for the CSV
    headers = ["Title", "PagerDuty Incident URL", "Slack Channel Name", "Slack Incident Post URL"]
    # Write to CSV file
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        for entry in filtered_entries:
            writer.writerow({
                "Title": entry["incident"]["summary"],
                "PagerDuty Incident URL": entry["incident"]["html_url"],
                "Slack Channel Name": entry["chat_channel_name"],
                "Slack Incident Post URL": entry["chat_channel_web_link"],
            })


def main():
    log_entries = get_log_entries()
    filtered_entries = filter_log_entries(log_entries)
    csv = generate_csv(filtered_entries)


if __name__ == "__main__":
    main()