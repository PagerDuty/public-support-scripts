import unittest
import requests
import sys
import csv
from unittest.mock import patch
sys.path.append('..')
import delete_features_with_csv

class test_stuff():
    def __init__(self):
        self.subdomain = "test_subdomain"

class DeleteResourceTest(unittest.TestCase):

    def setUp(self):
       delete_features_with_csv.options = {
        'subdomain': 'test_subdomain'
        
        }

    def test_construct_dictionary(self):
        dictionary_should_be = {
            "services": [ "P5G0L4E", "P26CKSR", "P9SOLH4"],
            "escalation_policies":[ "P9M61GH", "P0REPRD", "PZ4YTZJ", "P7AQQGT"],
            "schedules":[ "PZLRDOC", "PSCFBJM", "P0CTUZ1", "PWP3CZP"],
            "teams":[ "P8O2THQ", "PDHGVLE"],
            "users":[ "PW3C4JE", "POI33V1"]
        }



    def test_get_name(self):
        resource = "escalation_policies"
        # the schema of an esclation policy is much longer than this, but this will do for testing purposes    
        subscript = {
            "escalation_policy":{"id":"PAEILY8","type":"escalation_policy",
            "summary":"SN:CAB Approval","self":"https://api.pagerduty.com/escalation_policies/PAEILY8",
            "html_url":"https://pdt-isabella.pagerduty.com/escalation_policies/PAEILY8","name":"SN:CAB Approval",
            }
        }

        self.assertEqual(delete_features_with_csv.get_name(resource, subscript), "SN:CAB Approval")

    def test_make_plural(self):
        self.assertEqual(delete_features_with_csv.make_plural("escalation_policy"), "escalation_policies")
        self.assertEqual(delete_features_with_csv.make_plural("service"), "services")


             

    def test_delete_resources_and_dependencies(self):
        delete_features_with_csv.options.update({
            'delete_dependencies': True
            })
    




if __name__ == '__main__':
    unittest.main()