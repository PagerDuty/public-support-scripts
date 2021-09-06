#!/usr/bin/env python3

import requests
import argparse
import sys
import csv
import json


class WebhookGetter:
    def __init__(self, args):
        self.extension_url = f'https://api.pagerduty.com/extensions'
        self.subscription_url = f'https://api.pagerduty.com/webhook_subscriptions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={args.api_key}"
        }
        self.csv_file = args.backup_file
        self.v1_extension_schema_id = 'PF9KMXH'
        self.v2_extension_schema_id = 'PJFWPEP'
        self.webhook_version_list = [self.v1_extension_schema_id, self.v2_extension_schema_id] if args.version == 'all' \
            else [self.v1_extension_schema_id]

    @staticmethod
    def extract_v1v2_fields(webhook_object):
        """Extracts webhook url, filter id, description and other fields from v1/v2 
        webhook object to be copied to v3"""
        reduced_object = {'id': webhook_object['id'],
                          'extension_schema_id': webhook_object['extension_schema']['id'],
                          'url': webhook_object['endpoint_url'],
                          'description': webhook_object['name'],
                          'filter_id': webhook_object['extension_objects'][0]['id'],
                          'filter_type': webhook_object['extension_objects'][0]['type']}
        return reduced_object

    def write_json_to_csv(self, webhooks):
        """Creates a csv with webhook type, fields used for v3 webhook creation
        and full JSON payload of v1/v2 webhook"""
        for n, item in enumerate(webhooks[1]):
            fields_to_be_mapped = webhooks[1][n]
            full_webhook_object = webhooks[0][n]
            webhook_version = 'Generic Webhook V1' if item['extension_schema_id'] == self.v1_extension_schema_id \
                else 'Generic Webhook V2'
            with open(self.csv_file, 'a+') as file:
                writer = csv.writer(file)
                writer.writerow([webhook_version, fields_to_be_mapped, full_webhook_object])

    def test_connection(self):
        response = requests.get(self.extension_url + '?limit=1', headers=self.headers)
        try:
            status = response.status_code
            json_response = response.json()
            if status >= 400:
                print(f"ERROR: {status}\n       {json_response.get('error', 'error')}")
        except:
            print(response)
            sys.exit()
        finally:
            if response.status_code >= 400:
                sys.exit()

    def get_v1v2_webhooks(self):
        """Makes a GET request to /extensions endpoint, filters out generic v1/v2 webhooks
        and saves them in a nested list, with first item being a list of full webhook payloads and
        second item being a list of objects with fields to be used for webhook v3 creation"""
        self.test_connection()

        more = True
        offset = 0
        full_payload = []
        reduced_payload = []
        v1_v2_webhooks = []

        while more:
            response = requests.get(self.extension_url + f'?limit=100&offset={offset}', headers=self.headers).json()
            if len(response['extensions']) == 0:
                print('Found no webhooks to copy or delete')
            reduced_payload.extend(
                [self.extract_v1v2_fields(i) for i in response['extensions']
                 if i['extension_schema']['id'] in self.webhook_version_list])
            full_payload.extend(
                [i for i in response['extensions']
                 if i['extension_schema']['id'] in self.webhook_version_list])
            if not response['more']:
                more = False
            offset = offset + 100
        v1_v2_webhooks.append(full_payload)
        v1_v2_webhooks.append(reduced_payload)
        return v1_v2_webhooks

    def get_v3_webhooks(self):
        """Makes GET request(s) to /webhook_subscriptions endpoint, loops over the
        v3 webhooks returned and makes a key for each one with a combination of endpoint url,
        description, and service id and adds that key to a hash map which the function returns
        in order to later determine whether an about-to-be-created webhook subscription would 
        be a duplicate."""
        more = True
        offset = 0
        v3_webhooks = []
        existing_v3_webhooks_map = {}

        while more:
            response = requests.get(self.subscription_url + f'?limit=100&offset={offset}', headers=self.headers).json()
            v3_webhooks.extend(response.get('webhook_subscriptions', []))
            if not response['more']:
                more = False
            offset = offset + 100

        for webhook in v3_webhooks:
            # All v1/v2 will be service-related, so a concat of the endpoint + the service id 
            # + description will work for deduplication
            key = webhook['delivery_method']['url'] + webhook['filter']['id'] + webhook['description']
            existing_v3_webhooks_map[key] = True

        # send back the map
        return existing_v3_webhooks_map


class WebhookCreator:
    def __init__(self, args, v1_v2_webhook_list, v3_webhooks_map):
        self.baseurl = f'https://api.pagerduty.com/webhook_subscriptions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={args.api_key}"
        }
        self.v1_v2_webhooks = v1_v2_webhook_list
        self.existing_v3_webhooks = v3_webhooks_map
        if args.event_types == 'all-new':
            self.v3_events = json.loads('''{"events": [
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
                ]}''')
        else:
            self.v3_events = json.loads('''{"events": [
                                "incident.acknowledged",
                                "incident.annotated",
                                "incident.delegated",
                                "incident.escalated",
                                "incident.reassigned",
                                "incident.resolved",
                                "incident.triggered",
                                "incident.unacknowledged"
                            ]}''')
        self.v3_payload = json.loads('''{
            "webhook_subscription": {
                "delivery_method": {
                    "type": "http_delivery_method",
                    "url": ""
                },
                "description": "",
                "filter": {
                    "id": "",
                    "type": "service_reference"
                },
                "type": "webhook_subscription"
            }
        }''')
        self.v3_payload["webhook_subscription"]["events"] = self.v3_events["events"]

    def v3_webhook_already_exists(self, webhook_params):
        key = webhook_params['url'] + webhook_params['filter_id'] + webhook_params['description']
        if key in self.existing_v3_webhooks:
            print("Not creating a new v3 webhook for\n"
                  f"    endpoint: {webhook_params['url']}\n"
                  f"    service id: {webhook_params['filter_id']}\n"
                  f"    description: {webhook_params['description']}\n"
                  "  as it would be a duplicate of an existing v3 webhook.")
            return True
        return False

    def create_v3_webhook(self, webhook_params):
        """Constructs a v3 webhook payload"""
        v3_webhook = self.v3_payload
        v3_webhook['webhook_subscription']['delivery_method']['url'] = webhook_params['url']
        v3_webhook['webhook_subscription']['description'] = webhook_params['description']
        v3_webhook['webhook_subscription']['filter']['id'] = webhook_params['filter_id']
        return json.dumps(v3_webhook)

    def create_webhooks(self):
        """Creates v3 webhooks"""
        for webhook in self.v1_v2_webhooks:
            if self.v3_webhook_already_exists(webhook):
                continue
            data = self.create_v3_webhook(webhook)
            response = requests.post(self.baseurl, headers=self.headers, data=data)
            if 200 <= response.status_code < 300:
                print(f"""Created a v3 copy of webhook {webhook['id']} ({webhook['description']})
                on service {webhook['filter_id']}""")
            else:
                print(f"""ERROR: v3 copy of webhook {webhook['id']} ({webhook['description']}) on service
                {webhook['filter_id']} was not created\n"""
                      f"Received status code {response.status_code}\n")


class WebhookDeleter:
    def __init__(self, args, webhook_list):
        self.baseurl = f'https://api.pagerduty.com/extensions'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": f"Token token={args.api_key}"
        }
        self.webhooks = webhook_list

    def delete_v1v2webhooks(self):
        """Deletes v1/v2 webhooks"""
        for webhook in self.webhooks:
            response = requests.delete(self.baseurl + f"/{webhook['id']}", headers=self.headers)
            if 200 <= response.status_code < 300:
                print(f"""Deleted a webhook with {webhook['id']} ({webhook['description']})
                on service {webhook['filter_id']}""")
            else:
                print(f"""ERROR: a webhook with {webhook['id']} ({webhook['description']}) on service
                {webhook['filter_id']} was not deleted\n"""
                      f"Received status code {response.status_code}\n")


def main():
    ap = argparse.ArgumentParser(
        description="Migrate all v1/v2 webhooks to v3"
    )
    ap.add_argument('-k',
                    '--api-key',
                    required=True,
                    help='REST API key'
                    )
    ap.add_argument('-v', '--version',
                    required=False,
                    default='all',
                    choices=['all', 'v1'],
                    help="version(s) of the webhooks to copy or delete, 'all' is default")
    ap.add_argument('-e',
                    '--event_types',
                    required=False,
                    default='default',
                    choices=['default', 'all-new'],
                    help="'default' to create subscriptions to same types of events as previous versions of webhooks, or 'all-new' for all currently available types of events on Incident resource")
    ap.add_argument('-f',
                    '--backup_file',
                    required=False,
                    default='v1_v2_webhooks.csv',
                    help="filename to save information on retrieved v1/v2 webhooks, 'v1_v2_webhooks.csv' is default")
    ap.add_argument('-a',
                    '--action',
                    default='copy',
                    choices=['copy', 'delete'],
                    help="action to take on v1/v2 webhooks en masse, 'copy' is default")
    args = ap.parse_args()
    if args.action == 'copy':
        v1_v2_webhooks = WebhookGetter(args).get_v1v2_webhooks()
        v3_webhooks = WebhookGetter(args).get_v3_webhooks()
        WebhookCreator(args, v1_v2_webhooks[1], v3_webhooks).create_webhooks()
        WebhookGetter(args).write_json_to_csv(v1_v2_webhooks)
    elif args.action == 'delete':
        v1_v2_webhooks = WebhookGetter(args).get_v1v2_webhooks()
        WebhookGetter(args).write_json_to_csv(v1_v2_webhooks)
        WebhookDeleter(args, v1_v2_webhooks[1]).delete_v1v2webhooks()


if __name__ == "__main__":
    sys.exit(main())
