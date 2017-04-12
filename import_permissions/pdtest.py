"""module pdtest

Some labor-saving unit test methods in one place.
"""

from cStringIO import StringIO
import unittest
import sys


DEBUG = 0

class AdHocMock(object):
    """Basic mockery.

    Reinventing the wheel here because a dependency of the unittest.mock
    backport for Python 2.x has been deprecated by the PyPI maintainers and Mac
    OS X still does not come preinstalled with Python 3 but only has 2.7 
    """
    _calls = []
    _name = None
    _return_value = None

    def __init__(self, return_value=None, name="functional mock"):
        self._name = name
        self._return_value = return_value

    def __call__(self,*args,**kwargs):
        self._calls.append([args,kwargs.items()])
        if hasattr(self._return_value,'__call__'):
            return self._return_value(*args, **kwargs)
        else:
            return self._return_value

    def assert_call_count(self, count):
        assert count == len(self._calls), "Expected %d calls to %s, got %d"%(
            count, self._name, len(self._calls))

    def assert_called_with(self,*args,**kwargs):
        assert [args,kwargs.items()] in self._calls, ("Expected %s to have "+
            "been called with %s, but it was not. Calls = %s")%(
                self._name, str([args,kwargs.items()]), str(self._calls))

    def assert_calls(self, calls):
        assert calls == self._calls 
    

class TestCase(unittest.TestCase):

    _mocked_method_original_values = {}
    _mocked_objects = {}

    def setUp(self):
        # Suppress output:
        self.mock(sys,'stdout',StringIO())

    def mock(self, obj, attr, mockval):
        self._mocked_objects[id(obj)] = obj
        self._mocked_method_original_values[(id(obj),attr)] = getattr(obj,attr)
        setattr(obj, attr, mockval)

    def reset_mocks(self):
        for ((obj_id,attr), val) in self._mocked_method_original_values.items():
            setattr(self._mocked_objects[obj_id], attr, val)
        self._mocked_method_original_values = {}
        self._mocked_objects = {}

    def tearDown(self):
        sys.stdout.seek(0)
        output = sys.stdout.read()
        self.reset_mocks()
        if DEBUG and output.strip():
            print "===Command line output:==="
            print output
            print "===End output==="
