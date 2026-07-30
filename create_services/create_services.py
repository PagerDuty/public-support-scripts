# Copyright (c) 2019 PagerDuty
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Author: Lisa Yang (lyang@pagerduty.com) - PagerDuty Expert Services

import sys
import pdpyras
import csv
import json
import argparse



def create_services(api_token,dir):
    session = pdpyras.APISession(api_token)
    file = dir + '/' + 'create_service_list.csv'
    # csv headers
    H_S_NAME = 'name'
    H_S_DESCRIPTION = 'description'
    H_S_EP = 'escalation policy'
    H_S_URGENCY = 'notification urgency'
    H_S_ACK_TIMEOUT = 'acknowledgement timeout'
    H_S_AUTO_RESOLVE = 'auto resolution'
    H_S_INCIDENT_BEHAVIOR = 'incident behavior'

    with open(file, 'rU') as data_file:
        reader = csv.DictReader(data_file)

        for data in reader:
            s_name = data[H_S_NAME]
            s_description = data[H_S_DESCRIPTION]
            s_ep = data[H_S_EP]
            s_urgency = data[H_S_URGENCY]
            s_ack_timeout = data[H_S_ACK_TIMEOUT]
            s_auto_resolve = data[H_S_AUTO_RESOLVE]
            s_incident_behavior = data[H_S_INCIDENT_BEHAVIOR]

            service_record_number = 2
            escalation_policy = None
            escalation_policy = session.rget('escalation_policies', params={'query':s_ep})
            if escalation_policy is None:
                print('Escalation Policy {} did NOT exists'.format(s_ep))
                print('--->Service {} NOT Created\n'.format(s_name))
                service_record_number += 1

            else:
                service = session.rget('services', params={'query': s_name})

                if not service:
                    # service = self.add_service(data, service_record_number)

                    request_data = {}
                    data = {'service': request_data}
                    request_data['type'] = 'service'
                    request_data['name'] = s_name
                    request_data['description'] = s_description

                    if s_ack_timeout != '':
                        request_data['acknowledgement_timeout'] = get_timeout_in_seconds(
                            s_ack_timeout)
                    else:
                        request_data['acknowledgement_timeout'] = ''

                    if s_auto_resolve != '':
                        request_data['auto_resolve_timeout'] = get_timeout_in_seconds(s_auto_resolve)
                    else:
                        request_data['auto_resolve_timeout'] = ''

                    if s_incident_behavior.lower() == 'create alerts and incidents':
                        request_data['alert_creation'] = 'create_alerts_and_incidents'
                    if s_incident_behavior.lower() == 'create incidents':
                        request_data['alert_creation'] = 'create_incidents'

                    escalation_policy = {}
                    ep = session.rget('escalation_policies', params={'query':s_ep})
                    escalation_policy['id'] = ep[0]['id']
                    escalation_policy['type'] = 'escalation_policy_reference'
                    request_data['escalation_policy'] = escalation_policy

                    # incident urgency
                    incident_urgency_rule = {}

                    if s_urgency.lower() == 'severity':
                        incident_urgency_rule['type'] = 'constant'
                        incident_urgency_rule['urgency'] = 'severity_based'

                    if s_urgency.lower() == 'high':
                        incident_urgency_rule['type'] = 'constant'
                        incident_urgency_rule['urgency'] = 'high'

                    if s_urgency.lower() == 'low':
                        incident_urgency_rule['type'] = 'constant'
                        incident_urgency_rule['urgency'] = 'low'

                    request_data['incident_urgency_rule'] = incident_urgency_rule

                    support_hours = {}
                    support_hours['type'] = ''
                    request_data['support_hours'] = None

                    policy_exists = None
                    try:

                        policy_exists = session.rget('escalation_policies', params={'query':s_ep})
                        if policy_exists:

                            service = session.post('services', json=data)
                            if service['status_code'] == 201:
                                print(
                                    'Service: {} added'.format(s_name))
                                return service
                        else:
                            print('Escalation policy {} did NOT Exists.'.format(s_ep))
                            print('\tService {} was NOT Created\n'.format(s_name))

                    except Exception as e:
                        if not e:
                            print(str(e))



                else:
                    print("Service " + s_name + " existed")

            service_record_number += 1



def get_timeout_in_seconds(timeout_in_minutes):
    # parts = []
    # parts = timeout.split()
    # if parts[1].lower() == 'minutes':
    # timeout_in_seconds = int(parts[0]) * 60
    # if parts[1].lower() == 'hours':
    # timeout_in_minutes = int(parts[0]) * 60
    # timeout_in_seconds = timeout_in_minutes * 60
    timeout_in_seconds = int(timeout_in_minutes) * 60

    return timeout_in_seconds

if __name__=='__main__':
    ap=argparse.ArgumentParser(description="Creates PagerDuty Services on your PD Instance based off of list.")
    ap.add_argument("api_key", help="REST API key")
    ap.add_argument("dir", help="dir of your csv file")
    args = ap.parse_args()
    create_services(args.api_key,args.dir)