#!/usr/bin/env python

# Integration auto-setup script. WIP.

import argparse
import logging
import os
import subprocess
import sys

from pyzabbix import ZabbixAPI
from six import string_types
from six.moves import input

log = logging.getLogger()
session = None
debug = False

class Shell(object):

    prefix = ''
    """Command prefix, i.e. sudo/ssh"""

    queue = None
    """List of commands to be executed with the user's confirmation."""

    def __init__(self, prefix=None):
        if prefix is not None:
            self.prefix = prefix
        self.queue = []

    def prompt_yn(self, prompt):
        proceed = False
        while not proceed:
            proceed = input(prompt+' (y/n) ')
            if proceed:
                if proceed[0].lower() == 'y':
                    return True
                elif proceed[0].lower() == 'n':
                    return False
                else:
                    proceed = False

    def enqueue(self, command, stdin=None):
        """
        Enqueue a command for running before printing confirm dialog.

        :param command:
            The command to run
        :param stdin:
            If None, the process will not explicitly use any input stream. If a
            string object, that will be treated as its input.
        """
        if type(command) is not list:
            raise ValueError("Command must be list.")
        self.queue.append([command, stdin])

    def run_commands(self, noprompt=False, wd='.'):
        if not noprompt:
            do_it = self.prompt_yn("Run the following command(s)? \n"+
                '\n'.join([self.prefix+(' '.join(c[0])) for c in self.queue]))
        else:
            do_it = True
        if not do_it:
            return [-1]
        last_child = None
        while len(self.queue):
            command_spec = self.queue.pop(0)
            command = command_spec[0]
            stdin = command_spec[1]
            write_stdin = isinstance(stdin, string_types)
            if self.prefix:
                command.insert(0, self.prefix)
            pipe_to = None
            popen_kw = {'cwd':wd}
            # Handle pipe and other i/o options. Only one-step pipelines
            # currently supported; sorry.
            out_file = None
            if '>' in command:
                # Write output to a file
                split_pos = command.index('>')
                out_file = open(' '.join(command[split_pos+1:]), 'w+')
                command = command[:split_pos]
            if '|' in command:
                # Pipe to a secondary process
                popen_kw['stdout'] = subprocess.PIPE
                split_pos = command.index('|')
                pipe_to = command[split_pos+1:]
                # Add command prefix, i.e. sudo/ssh
                if self.prefix:
                    pipe_to.insert(0, self.prefix)
                command = command[:split_pos]
            if write_stdin:
                # We're going to write explicit input to the main process
                popen_kw['stdin'] = subprocess.PIPE
            # Start child process
            if pipe_to is None and out_file is not None:
                popen_kw['stdout'] = out_file
            last_child = subprocess.Popen(command, **popen_kw)
            if write_stdin:
                # Use a string object as STDIN for the current process, writing
                # input and then EOF to signify end of input.
                last_child.stdin.write(str.encode(stdin))
                last_child.stdin.close()
            if pipe_to is not None:
                # Pipe output to another child process
                popen_kw_2 = {'stdin':last_child.stdout, 'cwd':wd}
                if out_file is not None:
                    popen_kw_2['stdout'] = out_file
                pipe_to = subprocess.Popen(pipe_to, **popen_kw_2)
            # Clean up and conclude
            last_child.wait()
            if pipe_to is not None:
                pipe_to.wait()
            if out_file is not None:
                out_file.close()

class IntegrationSetup(Shell):

    install_method = 'opt'

    integration_scripts_path = '/usr/share/pdagent-integrations/bin'

    def install_pdagent(self):
        """Installs PagerDuty Agent"""
        if self.install_method == 'deb':
            # Install using apt-get
            log.info("Installing PagerDuty Agent via \"deb\" strategy.")
            self.enqueue(['apt-get', 'install', 'apt-transport-https'])
            r = requests.get('https://packages.pagerduty.com/GPG-KEY-pagerduty')
            if r.ok:
                self.enqueue(['apt-key', 'add'], stdin=r.text)
            else:
                raise Exception("HTTP error (%d) packages.pagerduty.com: %s"%(
                        r.status_code, r.text))
            self.enqueue(['tee', '/etc/apt/sources.list.d/pdagent.list'],
                stdin="deb https://packages.pagerduty.com/pdagent deb/")
        elif self.install_method == 'rpm':
            # Install using yum
            log.info("Installing PagerDuty Agent via \"rpm\" strategy.")
            rpm_config = """[pdagent]
name=PDAgent
baseurl=https://packages.pagerduty.com/pdagent/rpm
enabled=1
gpgcheck=1
gpgkey=https://packages.pagerduty.com/GPG-KEY-RPM-pagerduty
"""
            self.enqueue(['tee', '/etc/yum.repos.d/pdagent.repo'],
                stdin=rpm_config)
            self.enqueue(['yum', 'install', 'pdagent', 'pdagent-integrations'])
        elif self.install_method == 'opt':
            self.integration_scripts_path = idir+'/pdagent-integrations/bin'
            # Install from source to a local path
            log.info("Installing PagerDuty Agent from source to %s",
                self.integration_scripts_path)
            # Initial structure
            os.umask(0o22)
            idir = '/opt'
            self.enqueue(['mkdir', '-p', idir])
            # Download and unpack PagerDuty Agent
            self.enqueue(['curl', '-L', '-o', idir+'/pdagent.zip',
                'https://github.com/PagerDuty/pdagent/archive/master.zip'])
            self.enqueue(['unzip', '-d', idir, idir+'/pdagent.zip'])
            self.enqueue(['mv', idir+'/pdagent-master', idir+'/pdagent'])
            self.enqueue(['rm', idir+'/pdagent.zip'])
            # Download and unpack integration scripts
            self.enqueue(['curl', '-L', '-o', idir+'/pdagent-integrations.zip',
                'https://github.com/PagerDuty/pdagent-integrations/archive/master.zip'])
            self.enqueue(['unzip', '-d', idir, idir+'/pdagent-integrations.zip'])
            self.enqueue(['mv', idir+'/pdagent-integrations-master',
                idir+'/pdagent-integrations'])
            # Set up directories for ephemeral files
            self.enqueue(['mkdir', '-p', idir+'/pdagent/tmp'])
            self.enqueue(['chmod', '777', idir+'/pdagent/tmp'])
            self.enqueue(['ln', '-s', idir+'/pdagent/tmp', '/var/lib/pdagent'])
            self.enqueue(['chmod', '644', '/etc/pdagent.conf'])
            self.enqueue(['rm', idir+'/pdagent-integrations.zip'])
            # Put default config into place
            self.enqueue(['cp', idir+'/pdagent/conf/pdagent.conf', '/etc/'])
            #self.enqueue(['ln', '-s', idir+'/pdagent/pdagent
        self.run_commands()

class PDZabbixSetup(ZabbixAPI, IntegrationSetup):

    group_name = None
    dummy_host = None
    routing_key = None
    scripts_path = None

    def create(self, resource, filter_params, create_params):
        """
        Idempotent object creator function.

        Searches for an existing Zabbix configuration object of the given
        resource before creating it.

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
        Creates a very basic Zabbix host record for testing purposes.

        This will make it easier to create ad-hoc alerts to test the alert
        actions and make sure they work.

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
        """Guess the name Zabbix ID property name based on the resource type"""
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
        self.create_all_objects()
        self.install_pdagent()
        self.create_symlink()

    def create_all_objects(self):
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

    def create_symlink(self):
        """Create the symbolic link to the Zabbix alert script."""
        self.enqueue([
            'ln', '-s',
            os.path.join(self.integration_scripts_path, 'pd-zabbix'),
            os.path.join(self.zabbix_alert_scripts_path, 'pd-zabbix')
        ])
        self.run_commands()

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
        "automatically in a single script. Currently only supports Zabbix and "
        "requires direct access to the filesystem with the configuration.")
    # TODO: subcommands for other integration setups, i.e. Nagios
    ap.add_argument('-k', '--routing-key', required=True,
        help="Routing key, a.k.a. integration key, of the Zabbix integration "
        "in PagerDuty")
    ap.add_argument('-u', '--username', default='Admin',
        help="Zabbix user name for authenticating in the XMLRPC API")
    ap.add_argument('-p', '--password', default='zabbix',
        help="Zabbix user password for authenticating in the XMLRPC API")
    ap.add_argument('-b', '--zabbix-baseurl', default='http://127.0.0.1:8080',
        help="Base URL including protocol through port (if applicable). "
        "Must not include the initial trailing slash of the web root.")
    ap.add_argument('-d', '--dummy-host', default=None,
        help="Name of dummy host to create for testing the integration itself. "
        "If unspecified, no host will be created.")
    ap.add_argument('-g', '--group-name', default="Zabbix servers",
        help="Name of target host group; the PagerDuty user will be granted "
        "read-only access to this group of hosts.")
    ap.add_argument('-s', '--zabbix-alert-scripts-path',
        default='/etc/zabbix/alert.d',
        help="The Zabbix alert scripts path.")
    ap.add_argument('-i', '--install-method', default=None,
        help="If \"deb\", assume a Debian-like system and use deb/dpkg to "
        "install PagerDuty agent. If a path is provided instead, install from "
        "source at that path.")

    args = ap.parse_args()

    logging_init()

    # Configure Zabbix for the integration
    # TODO: switch/conditional w/other setup classes
    session = PDZabbixSetup(server=args.zabbix_baseurl)
    for attr in ('group_name', 'dummy_host', 'routing_key', 'scripts_path',
            'install_method'):
        if hasattr(session, attr):
            setattr(session, attr, getattr(args, attr))
    session.login(args.username, args.password)
    # Do all the things
    session.main()


if __name__ == "__main__":
    main()

