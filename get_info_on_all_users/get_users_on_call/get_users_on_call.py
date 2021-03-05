#!/usr/bin/env python

import argparse
import pdpyras
import sys
import csv

parameters = {}

def validate_arguments(args):
"""Make sure the command line arguments provided are the correct format and within date limitations"""
  for arg in args:
  	arg_format = type(arg)
	if arg == earliest:
	  if arg_format != bool: 
	    try_again_msg("earliest", arg, arg_format, bool)
	  else:   
	    parameters['earliest'] = arg
	elif arg == since:     

def try_again_msg(name_of_arg, provided_arg, provided_type, expected_type):
"""Helper function to say why the argument is wrong. todo: after message, prompt user to enter 
argument in the correct format."""
  wrong_format_message = "%s expects %s format; you provided %s, which is a %s value."
  sys.stdout.write(wrong_format_message.format(name_of_arg, expected_type, provided_arg, provided_type))


def populate_parameters_dictionary(args):
	for arg in args:
		if earliest:
			parameters['earliest'] = arg
		elif escalation_policies:
		    parameters['escalation_policies']	

def get_oncalls():
  oncalls = session.rget('/oncalls', params=parameters)
  # make a file and write results to it



if __name__ == '__main__':
  ap = argparse.ArgumentParser(description="Retrieves all users with the role(s) "
      "stated in the command line argument")
  ap.add_argument('-e', '--earliest', required=False, default=False, dest='parameters[earliest]',
  	help="only returns the earliest on-call for each combination of escalation policy escalation level; boolean type", 
  	action='store_true')
  ap.add_argument('-ep', '--escalation-policies', required=False, dest='escalation_policies',
  	help="takes a comma-separated list of escalation policy id's and filters results for on-calls in those policies")
  ap.add_argument('-sc', '--schedules', required=False, dest='schedules',
  	help="Takes a comma-separated list and filters the results, showing only on-calls for the specified schedule IDs")
  ap.add_argument('-u', '--users', required=False, dest='users',
  	help="Takes a comma-separated list and filters the results, showing only on-calls for the specified user IDs.")
  ap.add_argument('-si', '--since', required=False, dest='since', 
  	help="The start of the time range over which you want to search. cannot exceed 3 months. Format: date-time")
  ap.add_argument('-u', '--until', required=False, dest='since', 
  	help="The start of the time range over which you want to search. cannot exceed 3 months. Format: date-time")
  ap.add_argument('-t', '--timezone', required=False, dest='until', 
  	help="Time zone in which dates in the result will be rendered. format: \"tzinfo\" default: \"UTC\"")
  ap.add_argument('-f', '--filename', required=True, help="filename for csv", dest='filename')  	  
  ap.add_argument('-v', '--logging', default=False, dest='logging', help="verbose logging", action='store_true')  
  args = ap.parse_args()
  session = pdpyras.APISession(args.api_key)
  populate_parameters_dictionary(args)