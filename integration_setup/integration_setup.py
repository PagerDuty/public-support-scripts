#!/usr/bin/env python

# Integration auto-setup script. WIP.

import argparse
import logging
import sys

from pyzabbix import ZabbixAPI
from six.moves import input

log = logging.getLogger()
session = None
debug = False

#class Shell(object):
#
#    prefix = ''
#
#    def __init__(self, prefix=None):
#        if prefix is not None:
#            self.prefix = prefix
#
#    def prompt_yn(self, prompt):
#        proceed = False
#        while not proceed:
#            proceed = input(prompt+' (y/n) ')
#            if proceed:
#                if proceed[0].lower() == 'y':
#                    return True
#                elif proceed[0].lower() == 'n':
#                    return False
#                else:
#                    proceed = False
#
#    def run(self, command):
#        if type(command[0]) is str:
#            commands = [command]
#        elif type(command[0]) is list:
#            commands = command
#        else:
#            raise ValueError
#        do_it = self.prompt_yn("Run the following command(s)? \n"+
#            '\n'.join([self.prefix+(' '.join(c)) for c in command]))
#        if not do_it:
#            return [-1]
#        for command in commands:
#            command.insert(self.prefix, 0)
#            # TODO (finish)
#

class PDZabbixSetup(ZabbixAPI):

    group_name = None
    dummy_host = None
    routing_key = None

    def create(self, resource, filter_params, create_params):
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
        # Determine the name of the ID property:
        id_singular, id_plural = self.id_property_names(resource)
        api = getattr(self, resource)
        existing = api.get(**{'filter': filter_params})
        log.debug('Searching with filter params: %s', str(filter_params))
        if len(existing):
            log.info("Found one or more preexisting %s.", resource)
            return existing[0][id_singular]
        log.info("No preexisting %s found; creating a new one.", resource)
        result = api.create(**create_params)
        return result[id_plural][0]

    def create_testhost(self, hostname='dummy_host', grpname='Zabbix servers', 
            itemname='PagerDuty integration test'):
        """
        Creates a very basic host record for testing purposes.

        :param hostname:
            What to name the host
        :param grpname:
            Name of a group to use for the host. It must exist.
        """
        groups = self.hostgroup.get({'filter':{'name':[grpname]}})
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

    def id_property_names(self, resource):
        """Guess the name of the ID property based on the resource type"""
        id_property_name = resource
        # Work around antipatterns with special exceptions
        if resource=='usergroup':
            id_property_name = 'usrgrp'
        elif resource=='hostgroup':
            id_property_name = 'group'
        singular = id_property_name+'id'
        plural = singular+'s' # should be safe because noun is "id"
        return singular, plural

    def main(self):
        """
        Set up Zabbix objects for the PagerDuty to Zabbix integration
        """
        # Create the media type
        media_id = self.create('mediatype', {'description': 'PagerDuty'}, {
            'description': 'PagerDuty',
            'type': 1,
            'exec_path': 'pd-zabbix',
            'exec_params': '{ALERT.SENDTO}\n{ALERT.SUBJECT}\n{ALERT.MESSAGE}\n',
        })

        # Create a user group. It will be granted read access to the host group,
        # which must exist.
        usrgrpname = 'PagerDuty Service'
        group_id = self.create('usergroup', {'name': usrgrpname}, {
            'name': usrgrpname,
            'gui_access': '3',
            'rights': {
                'id': self.create('hostgroup', {'name': self.group_name}, {}),
                'permission': 2,
            }
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
        action_id = self.create('action', {'name': actionname}, {
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
        user_id = self.create('user', {'alias': alias}, {
            "alias": alias,
            "name": username,
            "surname": "",
            "usrgrps": [{'usrgrpid': group_id}],
            "refresh": "30s",
            "type": "1",
            "user_medias": [
                {
                    "mediatypeid": media_id,
                    "sendto": [self.routing_key],
                    "active": "0",
                    "severity": "63",
                    "period": "1-7,00:00-24:00"
                }
            ]
        })

        if self.dummy_host is not None:
            self.create_testhost(hostname=self.dummy_host,
                grpname=self.group_name)



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
    ap = argparse.ArgumentParser(description="Set up an on-premise integration "
        "automatically in a single script. Currently only supports Zabbix.")
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
    ap.add_argument('-d', '--dummy-host', default=None,
        help="Name of dummy host to create for testing the integration itself. "
        "If unspecified, no host will be created.")
    ap.add_argument('-g', '--group-name', default="Zabbix servers",
        help="Name of target host group; the PagerDuty user will be granted "
        "read-only access to this group of hosts.")
    args = ap.parse_args()

    logging_init()

    # Read access
    session = PDZabbixSetup(server=args.zabbix_baseurl)
    for attr in ('group_name', 'dummy_host', 'routing_key'):
        setattr(session, attr, getattr(args, attr))
    session.login(args.username, args.password)
    # Set everything up
    session.main()


if __name__ == "__main__":
    main()

