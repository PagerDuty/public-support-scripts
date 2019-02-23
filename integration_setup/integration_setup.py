#!/usr/bin/env python

# Load testing data thru RPC API

import argparse
import logging
import sys

from pyzabbix import ZabbixAPI

log = logging.getLogger()
session = None
debug = False

def create(resource, filter_params, create_params):
    """
    Idempotent object creator function.

    Searches for an existing object of the given resource before creating it.

    :param resource:
        The type of object, i.e. host
    :param filter_params:
        Parameters to use for searching for the preexisting object
    :param create_params:
        Parameters to use for creating the object
    :returns:
        The ID of the created resource
    """
    global session
    # Determine the name of the ID property:
    id_singular, id_plural = id_property_names(resource)
    api = getattr(session, resource)
    existing = api.get(**{'filter': filter_params})
    log.debug('Searching with filter params: %s', str(filter_params))
    if len(existing):
        log.info("Found one or more preexisting %s.", resource)
        return existing[0][id_singular]
    log.info("No preexisting %s found; creating a new one.", resource)
    result = api.create(**create_params)
    return result[id_plural][0]

def create_testhost(hostname='dummy_host', grpname='Zabbix servers', 
        itemname='PagerDuty integration test'):
    """
    Creates a very basic host record for testing purposes.

    :param hostname:
        What to name the host
    :param grpname:
        Name of a group to use for the host. It must exist.
    """
    global session
    groups = session.hostgroup.get({'filter':{'name':[grpname]}})
    if not len(groups):
        log.error("No host group '%s'; cannot create host entry.", grpname)
        return
    groupid = groups[0]['groupid']
    hostid = create('host', {'host': [hostname]}, {
        'host': hostname,
        'interfaces': [{
            'type': 1,
            'main': 1,
            'useip': 1,
            'ip': '127.0.0.1',
            'dns': '',
            'port': '10050'
        }],
        'groups': [{'groupid': groupid}],
    })
    # Create the item
    item_id = create('item', {'name': itemname}, {
        'name': itemname,
        'type': 2,
        'key_': 'test.timestamp',
        'hostid': hostid,
        'value_type': 4,
        'delay': '30s',
    })
    # Create the trigger; will create high-priority alerts
    triggername = itemname+' triggered'
    create('trigger', {'description': triggername}, {
        'description': triggername,
        'expression': '{%s:test.timestamp.diff()}>0'%hostname,
        'type': 1,
        'priority': 4,
    })

def id_property_names(resource):
    """Guess the name of the ID property based on the resource type"""
    id_property_name = resource
    # Work around antipatterns with special exceptions
    if resource=='usergroup':
        id_property_name = 'usrgrp'
    singular = id_property_name+'id'
    plural = singular+'s' # should be safe because noun is "id"
    return singular, plural

def logging_init():
    stdoutf = logging.Formatter("[%(asctime)s] [%(module)s:%(lineno)s] "
        "%(levelname)s: %(message)s")
    stdouth = logging.StreamHandler(sys.stdout)
    stdouth.setFormatter(stdoutf)
    log.addHandler(stdouth)
    log.setLevel(logging.INFO)
    if debug:
        log.setLevel(logging.DEBUG)

def main():
    global session
    ap = argparse.ArgumentParser()
    ap.add_argument('-k', '--routing-key', required=True,
        help="Routing key, a.k.a. integration key, of the Zabbix integration "
        "in PagerDuty")
    ap.add_argument('-u', '--username', default='Admin',
        help="Zabbix user name for authenticating in the XMLRPC API")
    ap.add_argument('-p', '--password', default='zabbix',
        help="Zabbix user password for authenticating in the XMLRPC API")
    ap.add_argument('-b', '--zabbix-baseurl', default='http://127.0.0.1:8080',
        help="Base URL including protocol through port (if applicable). "
        "Must not include the trailing slash.")

    args = ap.parse_args()

    logging_init()

    username = args.username
    password = args.password
    zabbix_base_url = args.zabbix_baseurl
    # Create a dummy host, item and trigger for integration testing
    test_host = True
    host_name = 'dummy_host'
    # Name of the host group to which the PagerDuty user group will be granted
    # read access
    group_name = 'Zabbix servers' 

    session = ZabbixAPI(server=zabbix_base_url)
    session.login(username, password)

    if test_host:
        create_testhost(hostname=host_name, grpname=group_name)


    # Create the media type
    media_id = create('mediatype', {'description': 'PagerDuty'}, {
        'description': 'PagerDuty',
        'type': 1,
        'exec_path': 'pd-zabbix',
        'exec_params': '{ALERT.SENDTO}\n{ALERT.SUBJECT}\n{ALERT.MESSAGE}\n',
    })

    # Create a user group
    usrgrpname = 'PagerDuty Service'
    group_id = create('usergroup', {'name': usrgrpname}, {
        'name': usrgrpname,
        'gui_access': '3',
    })

    # Create the alert action that will notify the user group on all media
    actionname = 'PagerDuty Notifications'
    msg_template = "name:{TRIGGER.NAME}\r\nid:{TRIGGER.ID}\r\nstatus:{TRIGGER.STATUS}\r\nhostname:{HOSTNAME}\r\nip:{IPADDRESS}\r\nvalue:{TRIGGER.VALUE}\r\nevent_id:{EVENT.ID}\r\nseverity:{TRIGGER.SEVERITY}"
    operation = {
        'operationtype': 0,
        'esc_period': '0',
        'esc_step_from': '1',
        'esc_step_to': '1',
        'evaltype': 0,
        'opconditions': [],
        'opmessage': {'default_msg': '1', 'mediatypeid': '0'},
        'opmessage_grp': [{'usrgrpid': group_id}],
    }
    action_id = create('action', {'name': actionname}, {
        'name': actionname,
        'eventsource': 0,
        'def_shortdata': 'trigger',
        'def_longdata': msg_template,
        'r_shortdata': 'resolve',
        'r_longdata': msg_template,
        'ack_shortdata': 'acknowledge',
        'ack_longdata': msg_template,
        'operations': [operation],
        'recovery_operations': [operation],
        'acknowledge_operations':[operation]
    })

    # Create the user in the group, with PagerDuty media
    username = 'PagerDuty User'
    alias = 'pagerduty'
    user_id = create('user', {'alias': alias}, {
        "alias": alias,
        "name": username,
        "surname": "",
        "usrgrps": [{'usrgrpid': group_id}],
        "refresh": "30s",
        "type": "1",
        "user_medias": [
            {
                "mediatypeid": media_id,
                "sendto": [args.routing_key],
                "active": "0",
                "severity": "63",
                "period": "1-7,00:00-24:00"
            }
        ]
    })

if __name__ == "__main__":
    main()

