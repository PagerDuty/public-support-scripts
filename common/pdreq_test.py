#!/usr/bin/env python

import requests
import pdtest
import pdreq

class APIConnection_test(pdtest.TestCase):

    api_key = 'Token_McTokenface'

    @property
    def essential_headers(self):
        return {
            'Authorization': 'Token token='+self.api_key,
            'Accept': 'application/vnd.pagerduty+json;version=2'
        }

    def test_get(self):
        api = pdreq.APIConnection(self.api_key)
        self.mock(requests,'get',pdtest.AdHocMock(name='APIConnection.get'))
        kw_in = {
            'params': {
                'query':'User McUserson',
                'include': ['contact_methods', 'notification_rules', 'teams']
            }
        }
        kw_out = kw_in.copy()
        kw_out.update({
            'headers': self.essential_headers
        })
        
        response = api.get('/users', **kw_in)
        requests.get.assert_called_with(
            'https://api.pagerduty.com/users',
            **kw_out
        )

    def test_post(self):
        headers = self.essential_headers.copy()
        headers.update({
            'Content-Type': 'application/json;charset=utf8'
        })
        api = pdreq.APIConnection(self.api_key)
        self.mock(requests,'post',pdtest.AdHocMock(name='APIConnection.post'))
        user = {'user': {
            'email': 'user@company.com',
            'name': 'User McUserson',
            'type': 'user',
            'role': 'manager' 
        }}
        api.post('/users', payload=user)
        headers_out = self.essential_headers.copy()
        headers_out.update({
            'Content-Type': 'application/json;charset=utf8'
        })
        requests.post.assert_called_with(
            'https://api.pagerduty.com/users',
            json=user,
            headers=headers_out,
            params={}
        ) 

    def test_get_object(self):
        """Tests object-lookup-by-name"""
        class response(object): status_code=200; json=lambda x: {
                    'objects_of_type': [
                        {'attr1': 'val1'},
                        {'attr1': 'val2 '}, # Test whitespace equivalence
                        {'attr1': 'VAL3'}, # Test case insensitive equivalence
                        {'attr1': 'VAL4 '} # Test both
                    ],
                    'more': False,
                }
        self.mock(
            requests, 
            'get', 
            pdtest.AdHocMock(
                name='requests.get',
                return_value=response()
            )
        )
        api = pdreq.APIConnection(self.api_key)
        # Strict equivalence
        obj = api.get_object(
            'objects_of_type', 
            'val1', 
            matchattr='attr1',
            match_case=True,
            match_space=True
        )
        self.assertEquals(obj,{'attr1': 'val1'})
        # Whitespace equivalence 
        obj = api.get_object(
            'objects_of_type',
            'val2',
            matchattr='attr1',
            match_case=True,
            match_space=False
        )
        self.assertEquals(obj,{'attr1': 'val2 '})
        # Test case insensitive equivalence
        obj = api.get_object(
            'objects_of_type',
            'val3',
            matchattr='attr1',
            match_case=False,
            match_space=True
        )
        self.assertEquals(obj,{'attr1': 'VAL3'})
        # Both case insensitivity and ignoring trailing/leadig space
        obj = api.get_object(
            'objects_of_type',
            'val4',
            matchattr='attr1',
            match_case=False,
            match_space=False
        )
        self.assertEquals(obj, {'attr1': 'VAL4 '})

        requests.get.assert_called_with(
            'https://api.pagerduty.com/objects_of_type',
            params={'query': 'val1', 'limit': 100, 'offset': 0},
            headers=self.essential_headers
        )


pdtest.unittest.main()
