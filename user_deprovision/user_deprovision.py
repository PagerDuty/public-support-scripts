#!/usr/bin/env python
#
# Copyright (c) 2018, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# PagerDuty Support asset: user_deprovision

import argparse
import json
import logging
import os
import time
import csv
from datetime import datetime

from six.moves import input
from pdpyras import APISession, PDClientError

log = logging.getLogger('user_deprovision')


def handle_exception(e):
    r = e.response
    if r is not None:
        r = e.response
        log.error("HTTP error %d: %s", r.status_code, r.text)
    else:
        log.exception(e)


def input_yn(message):
    """Prompt for a yes or no

    Summary: Prompt a y/n question
    Attributes:
        @param (prompt): question requiring y/n answer from user
    Returns: Boolean value of the user's answer
    """
    response = input(message + " (y/n): ").strip().lower()
    valid_responses = ('n', 'y')
    if response and response[0] in valid_responses:
        return bool(valid_responses.index(response))
    else:
        return input_yn(message)


class DeleteUser(APISession):
    """Class to handle all user deletion logic.
    
    REST API access methods are inherited from pdpyras.APISession.
    """

    def __init__(self, access_token, email, from_email, backup):
        super(DeleteUser, self).__init__(access_token, default_from=from_email)
        self.email = email
        self.backup = backup
        # Memoize user and set user_id property for convenience
        self.user_id = False
        if self.user is not None:
            self.user_id = self.user['id']

    def backup_object(self, url, modification):
        """
        Makes a backup file of an object.

        :param url:
            The URL to the resource to be backed up
        :param modification:
            The type of modification being made
        """
        if not os.path.isdir('backup'):
            os.mkdir('backup')
        now = int(time.time())
        if 'teams' in url:
            # Removed the user from team. Record that this was done
            user_id, team_id = url.split('/')[::-2][:2]
            filename = "removeduser-%s-fromteam-%s-%d" % (user_id, team_id, now)
            # Just create an empty file (TODO: retrieve and save team role)
            open(os.path.join('backup', filename), 'a').write('')
        else:
            # Save the object in a JSON file.
            obj = self.rget(url)
            filename = '%s-%s-%s-%d.json' % (modification, obj['type'], obj['id'],
                                             now)
            fh = open(os.path.join('backup', filename), 'w')
            json.dump(obj, fh)
            fh.close()

    def delete(self, url, **kw):
        """
        Delete an object, optionally making a backup first.
        """
        if self.backup:
            self.backup_object(url, 'deleted')
        return super(DeleteUser, self).delete(url, **kw)

    def delete_user(self):
        """Delete user from PagerDuty"""
        r = self.delete('users/' + self.user_id)
        return r.ok

    def list_open_incidents(self, additional_params=None):
        """
        Get any open incidents assigned to the user.

        :param additional_params:
            Parameters to send to the list incidents index. One could specify
            ``'date_range': 'all'`` to get all incidents and not just those that
            are recent, for instance, or restrict to certain service IDs using
            the ``service_ids[]`` parameter.
        """
        default_params = {
            'statuses[]': ['triggered', 'acknowledged'],
            'user_ids[]': self.user_id,
            'date_range': 'all'
        }
        if additional_params:
            default_params.update(additional_params)
        return self.list_all('incidents', params=default_params)

    def resolve_incidents(self, incidents):
        """
        Resolves a list of incidents.

        :param incidents:
            List of incident-like dict objects, i.e. retrieved from the API
        """
        for incident in incidents:
            log.info('Resolving %s', incident['id'])
            try:
                self.rput(incident['self'],
                          json={'type': 'incident_reference', 'status': 'resolved'})
            except PDClientError as e:
                handle_exception(e)
                log.error("Could not resolve incident %s.", incident['id'])

    @property
    def escalation_policies(self):
        """List all escalation policies user is on"""
        if not hasattr(self, '_escalation_policies'):
            self._escalation_policies = self.list_all('escalation_policies', params={'user_ids[]': self.user_id})
        return self._escalation_policies

    def list_users_on_team(self, team_id):
        """List all users on a particular team"""
        return self.list_all('users', params={'team_ids[]': team_id})

    def schedule_has_user(self, schedule):
        """Check if a schedule contains a particular user"""
        for user in schedule['users']:
            if user['id'] == self.user_id:
                return True
        return False

    def remove_from_escalation_policy(self, escalation_policy, obj=None):
        """
        Remove a user or schedule from an escalation policy's rules.

        :param escalation_policy:
            reference to the escalation policy to remove the user from
        :param obj:
            PagerDuty object or resource reference
        """
        if obj == None:  # Assume it's the user we want to remove
            obj = self.user
        obj_type = obj['type'].replace('_reference', '')
        new_rules = []
        for i, rule in enumerate(escalation_policy['escalation_rules']):
            new_targets = []
            for j, target in enumerate(rule['targets']):
                # Remove the target because it's being deleted
                if target['id'] == obj['id'] and \
                        target['type'].startswith(obj_type):
                    continue
                new_targets.append(target)
            # Remove the rule because it has no targets
            if not len(new_targets):
                continue
            rule['targets'] = new_targets
            new_rules.append(rule)
        escalation_policy['escalation_rules'] = new_rules
        return len(new_rules) > 0

    def remove_from_schedule(self, schedule):
        """
        Removes the user from a given schedule.

        :param schedule:
            Schedule dictionary object
        """
        new_layers = []
        not_empty = False
        for layer in schedule['schedule_layers']:
            # Get index of user in layer
            new_users = []
            for u in layer['users']:
                # Remove the user
                if u['user']['id'] == self.user_id:
                    continue
                new_users.append(u)
            # If this is the only user on the layer, end the layer now
            if not len(new_users):
                layer['end'] = datetime.now().isoformat()
            else:
                layer['users'] = new_users
                not_empty = True
            new_layers.append(layer)
        # Reverse the order before saving because of a known issue
        schedule['schedule_layers'] = new_layers[::-1]
        # Remove read-only property
        del schedule['users']
        return not_empty

    def remove_user_from_team(self, team_id):
        """Remove a user from a team"""
        try:
            self.rdelete('/teams/{team_id}/users/{user_id}'.format(
                team_id=team_id, user_id=self.user_id))
        except PDClientError as e:
            handle_exception(e)

    def team_has_user(self, team_users):
        """Check the users on a team for the deletion user"""
        for user in team_users:
            if user['id'] == self.user_id:
                return True
        return False

    def put(self, url, **kw):
        """
        Performs a put request, optionally making a backup first.
        """
        if self.backup:
            self.backup_object(url, 'updated')
        return super(DeleteUser, self).put(url, **kw)

    @property
    def user(self):
        if not (hasattr(self, '_user') and self._user):
            self._user = self.find('users', self.email,
                                   attribute='email')
        return self._user


def delete_user(access_token, user_email, from_email, prompt_del, auto_resolve,
                backup):
    """
    Deletes a PagerDuty user.

    Prompts for input when necessary to make decisions, i.e. whether to delete
    an escalation policy or schedule that will be empty after removing the user.

    :returns: integer 1 or 0 signifying whether the user was deleted
    """
    # Declare an instance of the DeleteUser class
    user_deleter = DeleteUser(access_token, user_email, from_email, backup)
    if user_deleter.user is None:
        log.error("Unable to find user matching email %s; skipping.",
                  user_email)
        return 0
    # Get the user ID of the user to be deleted
    user_id = user_deleter.user_id
    log.info('Deleting user: %(id)s (%(name)s <%(email)s>)',
             user_deleter.user)

    #############
    # Incidents #
    #############
    log.info("Checking for incidents assigned to user %s...", user_id)
    # Check for open incidents user is currently in use for
    incidents = user_deleter.list_open_incidents()
    n_incidents = len(incidents)
    if n_incidents > 0:
        # Determine if we want to auto-resolve them
        autores = auto_resolve or input_yn("There are currently %d open "
                                           "incidents that this user is assigned. Do you want to auto-resolve "
                                           "them? (y/n): " % n_incidents)
        if autores:
            log.info('Resolving all open incidents...')
            user_deleter.resolve_incidents(incidents)
            log.info('Successfully resolved all open incidents')
        else:
            log.critical("There are currently %d open incidents that this "
                         "user is assigned. Please resolve them and try again.",
                         n_incidents)
            log.info("The %s%d incidents assigned to this user are: ",
                     "first " if len(n_incidents) > 20 else "", n_incidents)
            for i in incidents[:20]:
                log.info(i['self'])
            return 0

    #######################
    # Escalation Policies #
    #######################
    log.info("Removing user %s from escalation policies...", user_id)
    escalation_policies = user_deleter.escalation_policies
    log.debug('Escalation policies: %s', ','.join(
        [e['id'] for e in escalation_policies]))
    for ep in escalation_policies:
        # Cache escalation policy
        user_deleter.remove_from_escalation_policy(ep)
        # Update the escalation policy. If it's empty, ask if the user wants to
        # delete the escalation policy
        if len(ep['escalation_rules']) != 0 or (
                prompt_del and not input_yn(
            "Escalation policy ID=%s, name=%s will be empty. Delete?" % (
                    ep['id'],
                    ep['name']
            )
        )):
            # Update the escalation policy
            try:
                # Delete description in case it is null
                del (ep['description'])
                user_deleter.rput(ep['self'], json=ep)
            except PDClientError as e:
                handle_exception(e)
        else:
            # Attempt to delete the empty EP otherwise:
            try:
                log.info("Escalation policy %s is empty after removing "
                         "the user; deleting it.", ep['id'])
                user_deleter.rdelete(ep['self'])
            except Exception:
                log.warning('Could not delete escalation policy %s. It no '
                            'longer has any on-call engineers or schedules but may '
                            'still be in use by services in your account.',
                            ep['name'])
    log.info("Finished escalation policies for user %s.", user_id)

    #############
    # Schedules #
    #############
    log.info("Removing user %s from schedules...", user_id)
    schedules = user_deleter.list_all('schedules')
    log.debug('Schedules: %s', ','.join([s['id'] for s in schedules]))
    for sched in schedules:
        # Get the specific schedule
        schedule = user_deleter.rget(sched['self'])
        # Check if user is in schedule
        if user_deleter.schedule_has_user(schedule):
            non_empty = user_deleter.remove_from_schedule(schedule)
            # If deleting, remove the schedule from any escalation policies
            if not non_empty and (prompt_del and input_yn(
                    ("Schedule (ID=%s, name=%s) will be empty after removing " \
                     "user. Delete it?") % (schedule['id'], schedule['name'])
            )):
                for ep_ref in schedule['escalation_policies']:
                    # Remove schedule from escalation policies...
                    ep = user_deleter.rget(ep_ref['self'])
                    user_deleter.remove_from_escalation_policy(ep, obj=sched)
                    # Update the escalation policy if there are rules or delete
                    # the escalation policy if there are none
                    if len(ep['escalation_rules']) > 0:
                        try:
                            log.info("Updating escalation policy " + ep['id'])
                            user_deleter.rput(ep['self'], json=ep)
                        except PDClientError as e:
                            handle_exception(e)
                    elif not prompt_del or input_yn((
                                                            "Escalation policy (ID=%s, name=%s) will be empty" \
                                                            "after removing the schedule to be deleted. " \
                                                            "Delete the escalation policy also?") % (
                                                            ep['id'], ep['name'])):
                        try:
                            log.info("Escalation policy %s will be empty "
                                     "after removing the schedule to be deleted "
                                     "(%s). The escalation policy will also be "
                                     "deleted.", ep['id'], schedule['id'])
                            user_deleter.rdelete(ep['self'])
                        except Exception:
                            log.warning("Escalation policy %s no longer "
                                        "has any on-call engineers or schedules but "
                                        "is still attached to services in your "
                                        "account. ", ep['id'])
                user_deleter.rdelete(schedule['self'])
            else:
                # Save updated schedule with user removed
                user_deleter.rput(schedule['self'], json=schedule)
    log.info("Finished schedules for user %s.", user_id)

    #########
    # Teams #
    #########
    log.info("Removing user %s from teams...", user_id)
    for team in user_deleter.iter_all('teams'):
        team_users = user_deleter.list_users_on_team(team['id'])
        if user_deleter.team_has_user(team_users):
            user_deleter.remove_user_from_team(team['id'])
    log.info("Finished teams for user %s.", user_id)

    ##################
    # Sayonara, User #
    ##################
    # Show the impact of removing the user:
    for resource in ('schedules', 'escalation_policies', 'teams'):
        label = resource.capitalize().replace('_', ' ')
        suffix = '/users/{id}' if resource == 'teams' else ''
        log.info('%s affected: %d', label, sum([
            user_deleter.api_call_counts.get(
                '%s:%s/{id}%s' % (method, resource, suffix), 0
            ) for method in ('put', 'delete')
        ]))
    if user_deleter.delete_user():
        log.info('User %s has been successfully removed!', user_email)
        return 1
    else:
        log.info('User %s not removed; aborted, or API error.', user_email)
        return 0


def main(arguments):
    email_list = []
    with open(arguments.user_csv) as file:
        for (i, row) in enumerate(csv.reader(file)):
            email = row[0].strip()
            # Skip blank emails 
            if not email:
                continue
            email_list.append(email)

    print("%d users to delete: %s" % (len(email_list), ', '.join(email_list)))
    # Prompt to fill in some gaps and confirm we want to continue:
    from_email = arguments.from_email
    if not arguments.from_email:
        from_email = input(
            "Please enter email address of the requesting agent: "
        ).strip()
    # Initialize logging:
    logdir = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(os.path.join(os.getcwd(), './logs')):
        os.mkdir(logdir)
    logfile = os.path.join(logdir, '%s.log' % datetime.now().isoformat())
    file_formatter = logging.Formatter(
        fmt=u"[%(asctime)s] %(levelname)s: %(message)s",
        datefmt=u"%Y-%m-%dT%H:%M:%S"
    )
    fileh = logging.FileHandler(logfile)
    fileh.setFormatter(file_formatter)
    log.addHandler(fileh)
    log.setLevel(logging.INFO)
    if arguments.verbose:
        stderrh = logging.StreamHandler()
        stderrh.setFormatter(logging.Formatter(u"%(levelname)s: %(message)s"))
        log.addHandler(stderrh)
        log.setLevel(logging.DEBUG)

    # Do the deed:
    count = 0
    for email in email_list:
        if arguments.prompt_del and not input_yn(
                "Proceed with deletion of user (%s)" % email):
            continue
        count += delete_user(arguments.access_token, email, from_email,
                             arguments.prompt_del, arguments.auto_resolve, arguments.backup)
    log.info("%d user(s) out of %d specified have been deleted." % (
        count, len(email_list)
    ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete a PagerDuty user')
    parser.add_argument(
        '--access-token', '-a',
        help="PagerDuty REST API access token",
        dest='access_token',
        required=True
    )
    parser.add_argument(
        '--users-emails-from-csv', '-u',
        help="File specifying list of users to delete. The file should be a CSV " \
             "with user(s) login email(s) in a single column.",
        dest='user_csv', type=str,
        required=True
    )
    parser.add_argument(
        '--from-email', '-f',
        help="Email address of the user requesting deletion",
        dest='from_email'
    )
    parser.add_argument(
        '--auto-resolve-incidents', '-r',
        help="Automatically resolve incidents assigned to the user.",
        dest='auto_resolve', action='store_true', default=False
    )
    parser.add_argument(
        '--delete-yes-to-all', '-y',
        help="When removing a user results in an empty object, i.e. an "
             "escalation policy with no rules, the script will prompt you as to "
             "whether you want to remove the empty object. Enabling this flag "
             "skips this prompting for deletion of objects and deletes all "
             "empty objects automatically.",
        dest='prompt_del', action='store_false', default=True
    )
    parser.add_argument(
        '--backup', '-b',
        help="Make backup JSON files of all objects that are deleted or "
             "updated, in a directory named 'backup' within the current working "
             "directory.",
        default=False, action='store_true'
    )
    parser.add_argument(
        '--verbose', '-v',
        help="Verbose command line output (show progress)",
        default=False, action='store_true'
    )
    args = parser.parse_args()
    main(args)
