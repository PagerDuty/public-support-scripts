#!/usr/bin/env python

import pdpyras
import unittest
import sys
from unittest.mock import MagicMock, patch

import rerole_users

class ReroleUsersTest(unittest.TestCase):

    ##############
    # Unit Tests #
    ##############
    def test_decide_new_roles(self):
        """
        Unit test of the individual
        """
        args = MagicMock()
        user = {'role':'user'}
        rerole_users.valid_roles = {
        'base': ['limited_user', 'user', 'admin', 'manager', 'observer', 
            'restricted_access', 'read_only_user', 'read_only_limited_user'],
        'team': ['observer', 'manager', 'responder']
    }
        # Command line args, no per-user
        args.new_base_role = 'observer'
        args.new_team_role = 'manager'
        args.adapt_roles = False
        self.assertEqual(
            ['observer', 'manager'],
            rerole_users.decide_new_roles(args, user, None, None)[:2]
        )
        # Command line args (w/adapt_users enabled): user->manager
        args.new_base_role = 'restricted_access'
        args.adapt_roles = True
        args.new_team_role = None
        self.assertEqual(
            ['restricted_access', 'manager'],
            rerole_users.decide_new_roles(args, user, None, None)[:2]
        )
        # Command line args (w/adapt_users enabled): limited_user->responder
        args.new_base_role = 'observer'
        user['role'] = 'limited_user'
        self.assertEqual(
            ['observer', 'responder'],
            rerole_users.decide_new_roles(args, user, None, None)[:2]
        )
        # Command line args (w/adapt_users enabled): restricted_access->None
        args.new_base_role = 'observer'
        user['role'] = 'restricted_access'
        self.assertEqual(
            ['observer', None],
            rerole_users.decide_new_roles(args, user, None, None)[:2]
        )
        # Per-user role overrides generic
        args.new_base_role = 'restricted_access'
        args.new_team_role = 'responder'
        self.assertEqual(
            ['restricted_access', 'responder'],
            rerole_users.decide_new_roles(args, user, 'restricted_access',
                'responder')[:2]
        )

    ####################
    # Functional Tests #
    ####################
    def test_rerole_users(self):
        """
        Test doing a "live" re-roling of users in an account w/API calls

        This is a very high-level test that depends on the notion that rerole
        operations are reversible using CSV files to back-up and restore.
        """
        global api_key
        if not api_key:
            return
        rbf = lambda i: 'rollback_%d.csv'%i
        rbtrf = lambda i: 'rollback_teams_%d.csv'%i
        rerole_users.session = pdpyras.APISession(api_key)
        args = MagicMock()
        args.assume_yes = True
        args.skip_roles = ['owner']
        # Step 1: Run a rerole then the inverse (WARNING: can mess up account)
        args.rollback_file = open(rbf(1), 'w')
        args.rollback_teamroles_file = open(rbtrf(1), 'w')
        args.all_users = True
        args.new_base_role = 'observer'
        args.new_team_role = 'responder'
        rerole_users.rerole_users(args) # Go
        # Step 2: Roll back (CSV file should trump all)
        args.all_users = False
        args.rollback_file.close()
        args.rollback_teamroles_file.close()
        args.roles_file = open(rbf(1), 'r')
        args.teamroles_file = open(rbtrf(1), 'r')
        args.rollback_file = open(rbf(2), 'w')
        args.rollback_teamroles_file = open(rbtrf(2), 'w')
        rerole_users.rerole_users(args) # Go
        args.roles_file.close()
        args.teamroles_file.close()
        # Step 3: Roll forward
        args.roles_file = open(rbf(2), 'r')
        args.teamroles_file = open(rbtrf(2), 'r')
        args.rollback_file = open(rbf(3), 'w')
        args.rollback_teamroles_file = open(rbtrf(3), 'w')
        rerole_users.rerole_users(args) # Go
        # Step 4: Roll back again and verify that the files are identical
        args.roles_file = open(rbf(3), 'r')
        args.teamroles_file = open(rbtrf(3), 'r')
        args.rollback_file = open(rbf(4), 'w')
        args.rollback_teamroles_file = open(rbtrf(4), 'w')
        rerole_users.rerole_users(args) # Go
        args.roles_file.close()
        args.teamroles_file.close()
        # If all was done properly, the rollback files in step 1 and 3 should be
        # idenetical (they reflect the roles in the account at the beginning)
        for rolefile in (rbf, rbtrf):
            self.assertEqual(open(rolefile(1), 'r').read(),
                open(rolefile(3), 'r').read())

if __name__ == '__main__':
    global api_key
    api_key = ''
    if len(sys.argv) > 1:
        api_key = sys.argv.pop()
    print("WARNING: functional testing, if it fails, will not automatically "
            "reset fixtures.")
    unittest.main()
