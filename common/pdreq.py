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

class PDRESTAPIError(Exception):
    
    def __init__(response, method, endpoint, params=[], body=None):
        message = "API responded with status {status} for {method} {endpoint}:"
        fmtvars = {
            'status': response.status_code, 
            'method': method, 
            'endpoint': endpoint
        }
        if params:
            message += " query params were {params};"
            fmtvars['params'] = '&'.join(
                ['{0}={1}'.format(*i) for i in params.items()]
            )
        if body is not None:
            message += " payload was: {body};"
            fmtvars['body'] = response.text
        self.message = message.format(**fmtvars)
        self.response = response

    def __str__(self):
        return self.message



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

    def __init__(self, token, from_email=None):
        self._token = token
        self._from_email = from_email
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

            if _base_url not in endpoint:
                url = _base_url+endpoint # Relative to base URL
            else:
                url = endpoint # Absolute URL
            kw = {
                'headers': {
                    'Accept': 'application/vnd.pagerduty+json;version=2',
                    'Authorization': 'Token token='+_token
                },
                'params': params
            }
            if _method in ('put','post'):
                kw['headers']['Content-Type'] = 'application/json;charset=utf8'
            if self._from_email:
                kw['headers']['From'] = self._from_email
            if payload is not None:
                kw['json'] = payload
            _api._requests.append((_method,endpoint))
            return getattr(requests,_method)(url, **kw)
        return req

    def get_object(self, plural_type, query, matchattr='name', match_case=False,
        match_space=False):
        """Obtains an object of a given type by querying it
     
        Raises an exception if the API responds w/error status. Returns False if
        no object was found by that query parameter. Returns the object itself
        if found, sans the {"[type]": ...} wrapper

        :plural_type: The name of the endpoint, and plural of the object type.
        :query: The query parameter to use
        :matchattr: Match this attribute of results against the query input
        :match_case: Perform case-sensitive match. By default, equivalence (when
            determining uniqueness of names) is case-insensitive, so the default
            is False.
        :match_space: Count trailing and leading whitespace. This should be
            left as False unless you really need it for some reason. The API
            (as of this writing) ignores spaces when it performs the uniqueness
            check to avoid name collisions, so we should assume anything with
            leading or trailing whitespace counts as equivalent.
        """
        results = self.get_all(plural_type, params={'query':query})
        preproc = []
        if not match_case:
            preproc.append('lower')
        if not match_space:
            preproc.append('strip')
        # Our equivalence function for comparison:
        equiv = lambda x, pp, i: (
            equiv(getattr(x, pp[i])(), pp, i+1) if i<len(pp) else x
        )
        # Our "match function" which should return true if the result value is
        # equivalent to  our query input per the rules defined in the options
        matchfn = lambda x: (
            equiv(x[matchattr], preproc, 0) == equiv(query, preproc, 0)
        )
        try:
            return iter(filter(matchfn, results)).next()
        except StopIteration:
            return False

    def get_all(self, plural_type, params={}, total=None):
        """Obtain all object records of a given type.

        Iterates through pagination and gets all instances of an object from the
        index endpoint

        :plural_type: The name of the endpoint, and plural of the object type.
        :params: Query parameters to pass to the API call. The `limit` parameter
            will be overridden.
        :total: If not none, must be an integer specifying the total overall
            number of objects to retrieve. If unspecified, it will return all.
        """
        p = {}
        p.update(params) # local working copy
        p['offset'] = 0
        if total is not None and total < 100:
            p['limit'] = total
        else:
            p['limit'] = 100

        results = []
        more = True
        
        while more:
            path = '/'+plural_type
            resp = self.get(path, params=p.copy())
            if resp.status_code // 100 != 2:
                raise PDRESTAPIError(resp, 'GET', path, params=p)
            rbody = resp.json()
            more = rbody['more']
            p['offset'] += p['limit']
            page = rbody[plural_type]
            results.extend(page)
            if type(total) is int and len(results) >= total:
                break

        return results

