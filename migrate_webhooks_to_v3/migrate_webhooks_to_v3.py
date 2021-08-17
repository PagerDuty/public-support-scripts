#!/usr/bin/env python3

import requests
import argparse
import sys
import csv
import json

V1_EXTENSION_SCHEMA_ID = 'PF9KMXH'
V2_EXTENSION_SCHEMA_ID = 'PJFWPEP'


class WebhookGetter:
    def __init__(self, args):
        self.baseurl = 'https://api.pagerduty.com/extensions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={args.api_key}"
        }
        self.csv_file = args.backup_file

    @staticmethod
    def extract_v1v2_fields(webhook_object):
        reduced_object = {'id': webhook_object['id'],
                          'url': webhook_object['endpoint_url'],
                          'description': webhook_object['name'],
                          'filter_id': webhook_object['extension_objects'][0]['id'],
                          'filter_type': webhook_object['extension_objects'][0]['type']}
        return reduced_object

    def write_json_to_csv(self, webhook_version, fields_to_be_mapped, full_webhook_object):
        #LOGIC FOR IDENTIFYING V1 / V2 VERSION OF THE WEBHOOK HERE
        with open(self.csv_file):
            writer = csv.writer(self.csv_file)
            writer.writerow([webhook_version, fields_to_be_mapped, full_webhook_object])


    def get_v1v2_webhooks(self):
        more = True
        offset = 0
        v1_v2_webhooks = []

        while more:
            response = requests.get(self.baseurl, headers=self.headers).json()
            v1_v2_webhooks.extend(
                [self.extract_v1v2_fields(i) for i in response['extensions']
                 if i['extension_schema']['id'] in [V1_EXTENSION_SCHEMA_ID, V2_EXTENSION_SCHEMA_ID]])
            if not response['more']:
                more = False
            offset = offset + 100
        return v1_v2_webhooks

class WebhookCreator:
    def __init__(self, args, webhook_list):
        self.baseurl = 'https://api.pagerduty.com/webhook_subscriptions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={args.api_key}"
        }
        self.webhooks = webhook_list
        self.v3_payload = json.loads('''{"webhook_subscription": {
        "delivery_method": {
            "type": "http_delivery_method",
            "url": ""
        },
        "description": "",
        "events": [
            "incident.acknowledged",
            "incident.annotated",
            "incident.delegated",
            "incident.escalated",
            "incident.priority_updated",
            "incident.reassigned",
            "incident.reopened",
            "incident.resolved",
            "incident.responder.added",
            "incident.responder.replied",
            "incident.status_update_published",
            "incident.triggered",
            "incident.unacknowledged"
        ],
        "filter": {
            "id": "",
            "type": "service_reference"
        },
        "type": "webhook_subscription"
    }
}''')

    def create_v3_webhook(self, webhook_params):
        v3_webhook = self.v3_payload
        v3_webhook['webhook_subscription']['delivery_method']['url'] = webhook_params['url']
        v3_webhook['webhook_subscription']['description'] = webhook_params['description']
        v3_webhook['webhook_subscription']['filter']['id'] = webhook_params['filter_id']
        return json.dumps(v3_webhook)

    def create_webhooks(self):
        for webhook in self.webhooks:
            data = self.create_v3_webhook(webhook)
            print(type(data))
            print(data)
            response = requests.post(self.baseurl, headers=self.headers, data=data)
            if 200 <= response.status_code < 300:
                print(f"""Created a v3 copy of {webhook['id']} ({webhook['description']})
                on service {webhook['filter_id']}""")
            else:
                print(f"""ERROR: v3 copy of {webhook['id']} ({webhook['description']}) on service
                {webhook['filter_id']} was not created\n"""
                      f"Received status code {response.status_code}\n")


def main():
    ap = argparse.ArgumentParser(
        description="Migrate all v1 and v2 webhooks to v3"
    )
    ap.add_argument('-k',
                    '--api-key',
                    required=True,
                    help='REST API key'
                    )
    ap.add_argument('-f',
                    '--backup_file',
                    required=True,
                    help='Filename to save information on retrieved v1/v2 webhooks')

    args = ap.parse_args()
    v1_v2_webhooks = WebhookGetter(args).get_v1v2_webhooks()
    WebhookCreator(args, v1_v2_webhooks).create_webhooks()


if __name__ == "__main__":
    sys.exit(main())