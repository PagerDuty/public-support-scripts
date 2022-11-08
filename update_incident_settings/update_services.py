#!/usr/bin/env python
import requests
import csv
import sys
import argparse

def update_services(args, services):
  api_key = args.api
  pdObjects = "services"
  
  url = f'https://api.pagerduty.com/{pdObjects}/' 

  headers = { 'Content-Type': 'application/json', 'Accept': 'application/vnd.pagerduty+json;version=2', 'Authorization': 'Token token='+api_key}
  
  for serviceID in services:
    responseJson = requests.get(url + serviceID, headers=headers).json()
    alert_creation = responseJson.get('service').get('alert_creation')
    name = responseJson.get('service').get('summary')
    srv_id = responseJson.get('service').get('id')
    
    if alert_creation != 'create_alerts_and_incidents':
      payload = {
        "service": {
          "alert_creation": "create_alerts_and_incidents"
      }}

      res = requests.put(url + serviceID, json=payload, headers=headers)
      if(res.status_code != 200):
        print(f"HTTP error {res.status_code}, {res.text} ")
      else:
         print(f"Updated the service ({srv_id}) - {name} ")
    else:
      print(f"Skipping ({srv_id}) - {name}")
      
    continue

def main():

  ## List argruments 
  parser = argparse.ArgumentParser()
  parser.add_argument('-k', '--api', help="pagerduty api token", required=True)
  parser.add_argument('-f', '--file', help="csv with Services Obfuscated ID fields", required=True )
  
  args = parser.parse_args()
 
  csv_data = []

  with open(args.file, 'r') as infile:
    reader = csv.reader(infile)
    for row in reader:
      try:
          csv_data.append(row[0])
      except KeyError:
          print("error")

  update_services(args,csv_data)

if __name__ == '__main__':
  sys.exit(main()) 
