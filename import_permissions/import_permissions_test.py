#!/usr/bin/env python

import logging
import pdtest
import pdreq
import import_permissions

pdtest.DEBUG = 0

class APIMock(object):

    def __init__(self,get=None, post=None, get_object=None):
        self.get = get
        self.post = post
        self.get_object = get_object

class get_object_mock(object):

    def __init__(self,return_values):
        self.return_values = return_values

    def __call__(self,plural, query, matchattr='name'):
        try:
            return iter(filter(
                lambda o: o[matchattr] == query,
                self.return_values[plural]
            )).next()
        except StopIteration:
            return False

class import_permissions_test(pdtest.TestCase):

    def test_logrow(self):
        self.mock(logging, 'warn', pdtest.AdHocMock(name='logging.warn'))
        self.mock(logging, 'debug', pdtest.AdHocMock(name='logging.debug'))
        msg = 'This and %s'
        import_permissions.logrow(msg,['a','b','c'],'that')
        logging.warn.assert_called_with(msg,'that')
        logging.debug.assert_called_with("Row: "+",".join(['a','b','c']))

    def test_parse_permissions(self):
        """Test compiling permissions from the CSV into roles API payloads

        Mainly want to run through, see if nothing breaks.
        """
        # What the mocked objects will return.
        # This is essentially our account fixture data:
        object_getter = get_object_mock({
            'users': [
                { # This guy: should throw an error and move on
                    'email': 'admin@test.com',
                    'role' : 'admin',
                    'id'   : 'PADMINID'
                },
                {  
                    'email': 'observer@test.com',
                    'role' : 'observer',
                    'id'   : 'POBSERVERID'
                },
                { 
                    'email': 'responder@test.com',
                    'role' : 'responder',
                    'id'   : 'PRESPONDERID'
                },
                { 
                    'email': 'manager@test.com',
                    'role' : 'manager',
                    'id'   : 'PMANAGERID'
                },
            ],
            'escalation_policies': [
                {
                    'name' : 'EP1',
                    'id'   : 'PEP1ID'
                }
            ],
            'services': [
                {
                    'name' : 'Service1',
                    'id'   : 'PSRV1ID'
                }
            ],
            'schedules': [
                {
                    'name' : 'Schedule1',
                    'id'   : 'PSCHD1ID'
                }
            ],
            'teams': [
                {
                    'name' : 'Team1',
                    'id'   : 'PTEAM1ID'
                }
            ]
        })

        # This is our test input:
        csv_iter = [
            ['admin@test.com','observer','team','Team1'], # print error/ignore
            ['admin@test.com','observer','team','Team1'], # print error/ignore
            ['nobody@test.com','observer','team','Team1'], # print error/ignore
            ['nobody@test.com','observer','team','Team1'], # print error/ignore
            ['observer@test.com','observer','team','Team2'], # print error/ignore
            ['observer@test.com','observer','team','Team2'], # print error/ignore
            ['observer@test.com','admin','team','Team1'], # print error/ignore
            ['manager@test.com','manager','team','Team1'],
            ['responder@test.com','responder','team','Team1'],
            ['responder@test.com','manager','escalation_policy','EP1'],
            ['responder@test.com','manager','schedule','PSCHD1ID'],
            ['observer@test.com','observer','team','Team1'],
        ]

        self.mock(import_permissions, 'API', APIMock(get_object=object_getter))
        import_permissions.logging_init(3)
        permissions = import_permissions.parse_permissions(csv_iter)

        # Uncomment this to view output and, once it looks good, use that output
        # as expected data:
        #print(permissions)

        # Sorta brittle, I know, but it's easiest to just check the structure by
        # sight, make sure it lines up with the input, paste the new value here
        # and move on.  
        #
        # The result should mimic the /users/{user_id}/roles schema:
        expected_permissions = {
            "PMANAGERID": {
              "roles": [
                {
                  "type": "role",
                  "role": "manager",
                  "resources": [
                    {
                      "type": "team_reference",
                      "id": "PTEAM1ID"
                    }
                  ],
                  "user_id": "PMANAGERID"
                }
              ]
            },
            "PRESPONDERID": {
              "roles": [
                {
                  "type": "role",
                  "role": "manager",
                  "resources": [
                    {
                      "type": "escalation_policy_reference",
                      "id": "PEP1ID"
                    },
                    {
                      "type": "schedule_reference",
                      "id": "PSCHD1ID"
                    }
                  ],
                  "user_id": "PRESPONDERID"
                },
                {
                  "type": "role",
                  "role": "responder",
                  "resources": [
                    {
                      "type": "team_reference",
                      "id": "PTEAM1ID"
                    }
                  ],
                  "user_id": "PRESPONDERID"
                }
              ]
            },
            "POBSERVERID": {
              "roles": [
                {
                  "type": "role",
                  "role": "observer",
                  "resources": [
                    {
                      "type": "team_reference",
                      "id": "PTEAM1ID"
                    }
                  ],
                  "user_id": "POBSERVERID"
                }
              ]
            }
        }
        self.assertItemsEqual(expected_permissions, permissions)
pdtest.unittest.main()