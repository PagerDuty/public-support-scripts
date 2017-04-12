"""PDReq

A super-lightweight PagerDuty v2 REST API client.

Built around the requests module; this is a thin wrapper that performs the
tedious tasks like headers and keyword argument setting so that it's easier to
just get, post, put and delete to the API.

Instances of the the APIConnection object will have callable attributes named
after each of the standard HTTP verbs. The methods take one positional argument,
"endpoint", and optional keyword arguments "params" (URL parameters to append to
the endpoint) and "payload" (the object to be JSON-encoded and sent as the
request body). The return value will then be an instance of requests.Response.

Refer to: 
http://docs.python-requests.org/en/master/user/advanced/#request-and-response-objects

Usage:

from pdreq import APIConnection

# Create an API connection object:
api = APIConnection('<your API key here>')

# Get account abilities:
response = api.get('/abilities')
print "Account abilities: "+", ".join(response.json()['abilities'])

# Create a user:
response = api.post("/users", payload = {"user": {
    "name": "User McUserson",
    "email": "user@company.com",
    "type": "user",
    "role": "manager" 
}})

# Error handling:
if response.status_code // 100 == 2:
    print "Created user!"
else:
    print "Error in request: Status %d, body = %s"%(
        response.status_code,
        response.text
    )
"""

import requests

_http_verbs = ('get','post','put','delete')

class APIConnection(object):

    _token = None
    _requests = None

    def __getattribute__(self, attr):
        if attr[0]=='_' or hasattr(APIConnection,attr):
            return super(APIConnection, self).__getattribute__(attr)
        elif attr in _http_verbs:
            return super(APIConnection, self).__getattribute__(
                '_api_request'
            )(attr)
        else:
            raise AttributeError("APIConnection object has no attribute: "+attr)

    def __init__(self, token):
        self._token = token
        self._requests = []

    def _api_request(self, method):
        """Generic API method constructor."""
        _api = self
        _method = method
        _token = self._token
        _base_url = 'https://api.pagerduty.com'
        def req(endpoint, params={}, payload=None):
            """Make an API request and return the requests object.
            
            :endpoint: The API endpoint to use.
            :params: URL parameters to include
            :body: The object to be JSON-encoded and sent as the payload
            """
            url = _base_url+endpoint
            kw = {
                'headers': {
                    'Accept': 'application/vnd.pagerduty+json;version=2',
                    'Authorization': 'Token token='+_token
                },
                'params': params
            }
            if _method in ('put','post'):
                kw['headers']['Content-Type'] = 'application/json;charset=utf8'
            if payload is not None:
                kw['json'] = payload
            _api._requests.append((_method,endpoint))
            return getattr(requests,_method)(url, **kw)
        return req

    def get_object(self, plural_type, query, matchattr='name'):
        """Obtains an object of a given type by querying it
     
        Raises an exception if the API responds w/error status. Returns False if
        no object was found by that query parameter. Returns the object itself
        if found, sans the {"[type]": ...} wrapper

        :plural_type: The name of the endpoint, and plural of the type.
        :query: The query parameter to use
        :matchattr: Match this attribute of results exactly against the query input
        """
        resp = self.get('/'+plural_type, params={'query':query})
        if resp.status_code // 100 == 2:
            try:
                return iter(filter(
                    lambda o: o[matchattr] == query, 
                    resp.json()[plural_type]
                )).next()
            except StopIteration:
                return False
        else:
            raise Exception(("API responded with status %d for GET /%s with "+
                "query=%s")%(resp.status_code, plural_type, query))




