import sys
import csv
import requests 
import json
import os
from getpass import getpass
from datetime import datetime as dt
from pdpyras import APISession
from collections import OrderedDict
import logging
log = logging.getLogger('resource_deleter')

# delete_dependencies is for deleting objects which are interfering with the deletion of csv-named objects
# this variable defaults to false, but at beginning of program, TSE will be asked to set the value
delete_dependencies = False
account = None
current = dt.now()
date = "{}-{}".format(current.month, current.day)
time = "{}:{}".format(current.hour, current.minute)
now = "{}-{}".format(date, time)
deleted_resources = ""
backup_file = ""
error_log = ""
headers = {}
base_url = "https://api.pagerduty.com"


def logging_init(verbose, log_file):
    """
    Starts up logging.

    :param verbose:
        If true, set log level to debug. Otherwise, use level info.
    :param log_file:
        If set to a file object, add a stream handler to log to it.
    """
    global log
    global stdouth
    stdoutf = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stdouth = logging.StreamHandler(sys.stdout)
    stdouth.setFormatter(stdoutf)
    log.addHandler(stdouth)
    if log_file:
        fileh = logging.StreamHandler(log_file)
        fileh.setFormatter(stdoutf)
        log.addHandler(fileh)
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)


def construct_dictionary():
  """ 
  Summary: Takes objects named on CSV and puts them in a dictionary where object type is the key
  and id is the value. Dictionary is ordered in such a way to minimize dependency errors when iterating 
  through later in delete_resource 
  """
  csv_file_name = sys.argv[1]
  csv_file = open(csv_file_name)
  to_delete_dict = OrderedDict()
  object_type_lst = ["services", "extensions", "escalation_policies", "schedules", "teams", "users"]
  for object_type in object_type_lst:
    to_delete_dict[object_type] = []

  for row in csv_file:
    row = row.rstrip()
    resource_id, resource_type = row.split(',')
    resource_type = resource_type.lstrip()
    if resource_type in object_type_lst:
      to_delete_dict[resource_type] = to_delete_dict.get(resource_type, []) + [resource_id]
    # avoid making futile calls to nonexistent endpoints  
    else:  
      invalid_type_msg = f"\nERROR: \"{resource_type}\" is either not a valid endpoint or not a valid object."
      log.error(invalid_type_msg)
      write_to_log(error_log, invalid_type_msg)
    

  csv_file.close()
  
  return to_delete_dict


def get_session(key):
    global _sessions
    if key not in _sessions:
        _sessions[key] = APISession(key)
    return _sessions[key]	


def do_prompt_yn(prompt):
  """
  Function: do_prompt_yn
  Summary: Prompt a y/n question
  Attributes:
    @param (prompt): The question everyone is asking
  Returns: Boolean value of the user's answer
  """
  response = input("{0}? y/n: ".format(prompt))

  if response.lower() == 'y':
    return True
  elif response.lower() == 'n':
    return False
  else:
    return do_prompt_yn(prompt)


def do_prompt_value(prompt):
  """
  Function: do_prompt_value
  Summary: Makes a command line prompt
  Attributes:
    @param (prompt): The question
  Returns: String response from the user
  """
  response = input("{0}: ".format(prompt))
  return response


def write_to_log(log_name, log_message):
  """
  Function: write_to_log 
  Summary: takes name of file and string, writes string to the file, and
  closes file
  Attributes:
     @param (log_name): the name of the log being appended with message
     @param (log_message): the string to write to the log
  """
  with open(log_name, 'a') as file:
    file.write(log_message)


def get_name(resource, subscript):
  # takes resource type and subscriptable response object, returns name
  log.debug(subscript)
  if resource == "escalation_policies" or resource == "schedules":
    subkey = "summary"
  elif resource == "incident":
    subkey = "title"  
  else:
    subkey = "name"
  for key in subscript.keys():
      name = subscript[key][subkey]
  return name


def make_plural(resource_type):
  # simple helper function to reduce repetition
  if resource_type == "escalation_policy":
    return "escalation_policies"
  else:
    return resource_type + "s"  


def delete_resource(to_delete_dict):
  """ 
  SUMMARY: Goes through dictionary and deletes csv-named objects
  @param (to_delete_dict): dictionary of objects to delete - i.e. object_type : object_id
  """
  # each log is divided into sections by to object type; i.e. top section is services, then escalation
  # policies, etc
  for resource in to_delete_dict.keys():
    log.info("\n\n ---{}--- \n\n".format(resource))
    write_to_log(deleted_resources, "\n\n---{}---\n\n".format(resource))

    write_to_log(error_log, "\n\n\n---{}---\n".format(resource))
    log.info("there are {} {} to delete\n\n".format(len(to_delete_dict[resource]), resource))
    # goes through each id in the list of id's for a given object type
    for item in to_delete_dict[resource]:
      log.info("Deleting {} {}".format(resource, item))
      path = "{}/{}/{}".format(base_url, resource, item)
      # before we delete something, we get a backup of it to record to the backup log
      backup = requests.request('GET', path, headers=headers)
      # make a subscriptable version of the backup so we can look up particular key/value pairs in it 
      backup_subscriptable = backup.json()

      if backup.status_code == 200:
        name = get_name(resource, backup_subscriptable)
        response = requests.delete(path, headers=headers)
        handle_response(resource, response, path, item, backup, name)

      elif backup.status_code == 404:
        error_404 = (f"\n\n{backup.status_code} ERROR: {resource} {item} could not be found; may have already been" 
                    " deleted by previous execution or this script, or may be a typo.")
        log.error(error_404)
        write_to_log(error_log, error_404)

      else:
        special_error = f"Unable to get item {item}. Get response is: {backup.status_code}, {backup.text}"  
        log.error(special_error)
        write_to_log(error_log, special_error)


# may have made this function to simplify writing tests...      
def handle_response(resource, response, path, item, backup, name):
  """ 
  SUMMARY: Takes response (and a bunch of other object info) and figures out
  what to do next based on the object type and response status code 
  @param (resource): tyoe if object being deleted (i.e. service, escalation policy, etc.)
  @param (response): the request response from trying to delete the object
  @param (path): the URL that the request was made to
  @param (item): the ID of the individual object being deleted
  @param (backup): a schema of the ill-fated object, retrieved from a get request, for the purposes
        of recording to a backup log in case customer wants to recreate it later
  @param (name): name of the object being deleted      
  """
  # if delete request was unsuccessful and was for a service, escalation policy, schedule, or user
  if response.status_code == 400 and resource != "teams":
    # get info about the object we are trying to delete
    item_info = requests.request('GET', path, headers=headers)
    # enables dictionary like lookup for response from original delete request
    error_response = response.json() 
    # get the name for more readable logging information
    name = get_name(resource, item_info.json())
    # call function to handle errors
    status_code = response.status_code
    handle_error(resource, error_response, path, item, item_info, name, status_code)
  elif response.status_code == 400 and resource == "teams" and delete_dependencies:
    # teams are a bit more complicated, so they have their own function
    remove_team_dependencies(response, item)  
  elif response.status_code >= 200 and response.status_code <= 204:
    # if delete request was successful, record the object's schema to the backup log
    write_to_log(backup_file, "\n{} \n\n {} \n".format(resource, backup.text))
    # add the object's name to deleted resources log
    write_to_log(deleted_resources, name + "\n")
    # print a happy message for the TSE
    log.info("\nSUCCESS!\n\n")
  else: 
    # pretty sure ever possible outcome is accounted for above, but if not, useful info will
    # print and record to error log in case of something unexpected 
    log.error(f"status code is {response.status_code}")
    log.error(f"response is {response.text}")
    write_to_log(error_log, f"response {response.status_code}: {response.text}")    


def remove_team_dependencies(response, item):
  """
  @param (response): the request response from trying to delete a particular team
  @param (item): the id of the team that the program could not successfully delete in delete_resource():
  SUMMARY: like handle_error(), but specifically for tems; find out which escalation policies 
  are attached to the team we are trying to delete, and add each ep id to a list. Only gets called
  if two conditions are met: 1) there is a csv-named team that is associated with an escalation policy and
  2) the tse at the beginning opted to remove dependencies 
  """
  url = "{}/escalation_policies?team_ids%5B%5D={}&sort_by=name".format(base_url, item)
  team_eps = requests.request('GET', url, headers=headers)
  subscriptable_team_ep = team_eps.json()
  escalation_policies_to_delete = []
  for escalation_policy_instance in subscriptable_team_ep['escalation_policies']:
    escalation_policies_to_delete.append(escalation_policy_instance['id'])
  log.info(escalation_policies_to_delete)
  # go through list of ep id's and remove each ep from the team we are trying to delete
  for ep in escalation_policies_to_delete:
    path = "{}/teams/{}/escalation_policies/{}".format(base_url, item, ep)
    log.info(f"\nRemoving escalation policy {ep} via {path}")
    eps_removed_response = requests.delete(path, headers=headers)
    log.info(eps_removed_response.status_code)
    log.info("Reattempting to delete team ", item)
    path = "{}/teams/{}".format(base_url, item)
    
    team_info = requests.request('GET', path, headers=headers)
    team_subscript = team_info.json()
    name = get_name("teams", team_subscript)

    response = requests.delete(path, headers=headers)
    # if able to delete escalation policy attached to the team, print success, backup the escalation
    # policies to a log, and record their names to a log
    if response.status_code == 204:
      log.info("\nSUCCESS!\n\n")
      write_to_log(backup_file, "\nteams \n\n {} \n".format(team_info.text))
      write_to_log(deleted_resources, name + "\n")
    else:
    # if unable to delete escalation policy attached to team, tell the TSE and record the error response
    # to the error log 
      log.info(f"\nERROR: COULD NOT DELETE TEAM {item}, {name}")  
      write_to_log(error_log, f"\n\nUnable to delete # {item}, {name} because:\n\n {response.status_code}: {response.text}")    


def handle_error(resource, error_response, path, item, item_info, name, status_code):
  """ 
  Tries to programatically look up which resources need to be changed for successful deletion
  @param (resource): just the resource type; services / escalation_policies / schedules / teams / users
  @param (error_response): the subscriptable request response from the original attempt to delete the item
  @param (path): goes to the exact address of the object we are trying to delete
  @param (item): the id of object we are trying to delete
  @param (status_code): the status code of the request response
 
  """

  if resource != "escalation_policies" and resource != "users":
    for error in error_response['error']['errors']:
      log.error(error)
# if dependencies associated with the object are to be kept as is, then record the error to the error log
      if not delete_dependencies:
        write_to_log(error_log, error)

  if resource == "users":
    for conflict in error_response['error']['conflicts']:
      error_msg = conflict['type'] + ": " + conflict['id']
      log.error(error_msg)
# if conflicting dependencies associated with the user are to be kept as is, then record the error to the error log
      if not delete_dependencies and conflict['type'] == 'incident':   
        write_to_log(error_log, f"{error_response.status_code}: unable to delete user {name} because of they have the following open incidents:\n" + error_msg)
      elif not delete_dependencies:
        conflict_type_plural = make_plural(conflict['type'])
        url = base_url + f"""/{conflict_type_plural}/{conflict['id']}"""
        conflicting_object = requests.request('GET', url, headers=headers)
        subscriptable_conflict = conflicting_object.json()
        conflict_name = get_name(conflict_type_plural, subscriptable_conflict)
        write_to_log(error_log, f"\n{status_code} ERROR: unable to delete user {name} because of they are in the following {conflict['type']}: {conflict_name}")     

  # if at beginning of program, engineer selected to delete any dependent resources, this will delete
  # the appropriate escalation policies, schedules, etc 
  if delete_dependencies:
    log.debug("calling function to remove dependencies...")
  # if able to delete the resources associated with the csv-named resource, make a second request to delete the
  # csv named resource  
    if remove_dependencies(resource, item, error_response, path):
      log.info(f"attempting to delete {resource} {info} again after removing dependencies...")
      second_attempt = requests.delete(path, headers=headers)
      log.info(f"second attempt: {second_attempt.status_code}")
  # if second attempt at deleting csv-named resource is successful, back up the resource and add its name to the
  # appropriate files    
      if second_attempt == 204:
        write_to_log(backup_file, item_info.text)
        write_to_log(deleted_resources, name)
  # if second attempt is not successful, record error to error log      
      else: 
        write_to_log(error_log, f"\n{second_attempt.status_code}: {second_attempt.text}")  
    
  # if delete request for an escalation policy failed, and TSE chose to leave dependencies intact 
  # at beginning of program, print out which services are using the escalation policy and record 
  # those services to the error log, explaining that the escalation policy must be removed from those
  # services before it can be deleted
  elif resource == "escalation_policies" and delete_dependencies == False:
    info = requests.request('GET', path, headers=headers)
    info_subscript = info.json()
    log.error("\n\nERROR: Unable to delete escalation policy because it csontains the following service(s):")
    for key in info_subscript:
      service = info_subscript[key]['services']
      services_to_remove = []
      for service in info_subscript[key]['services']:
        services_to_remove.append(service['summary'])
      message = (f"\n\nIn order to delete escalation policy {item}, {info_subscript[key]['summary']}," 
        "you must first go into the web app and remove it from the following service(s):")
      log.info(message)
      for service_name in services_to_remove: log.info(service_name)
      write_to_log(error_log, message+"\n\n")
      write_to_log(error_log, ('\n').join(services_to_remove))
 

def resolve_incident(incident_id):
  """
  Summary: if a user or escalation policy can't be deleted because they have an open incident,
  this function will be called to resolve that incident
  @param (incident_id): the id of the incident to be deleted
  """

  headers["Content-type"] = "application/json"
  payload = {
  "incident": {
    "type": "incident_reference",
    "status": "resolved"
    }
  }
  path = "{}/incidents/{}".format(base_url, incident_id)
  log.debug(path)
  log.debug(payload)
  incident_response = requests.put(path, data=json.dumps(payload), headers=headers)
  # return request response so can check if incident was successfully resolved
  return incident_response


def remove_dependencies(resource, item, subscriptable, path):
  """
  Summary: looks up and deletes resources dependent on the csv-named resource to be deleted
  @param (resource): the type of resource we are trying to remove named on the csv
  @param (item) : the id of the resource we are trying to removed, named on the csv
  @param (subscriptable) : a subscriptable dictionary of the response from originally trying to delete the resource in delete_resource()
  @param (path) : goes to individual resource we tried to delete in delete_resource(), i.e. "https://api.pagerduty.com/{resource}/{item}
  """
  # counter variables to keep track of how many conflicts there are vs. how many get removed
  conflicts = 0
  conflicts_removed = 0
  dependencies_removed = False 
  log.info("Removing dependencies")
  if resource == "escalation_policies":
    info = requests.request('GET', path, headers=headers)
    info_subscript = info.json()
    for item_dict in info_subscript['escalation_policy']["services"]:
      # for each 
      conflicts += 1
      url = "{}/services/{}".format(base_url, item_dict["id"])
      # get a backup of the service before trying to delete it
      deleted_service = requests.request('GET', url, headers=headers)
      attempt = requests.delete(url, headers=headers)
      # print out the response from the delete request (will only have content if request 
      # did not work)
      log.info(attempt.text)
      if attempt.status_code == 204:
        ep_name = get_name(resource, info_subscript)
        service_name = get_name("services", deleted_service.json())
        # write to back up log and the log that lists names of deleted things, and explain why it was deleted since it wasn't named on the csv
        write_to_log(backup_file, f"\nService deleted so escalation policy {item}, {ep_name}, can be deleted: \n\n {deleted_service.text} \n")
        write_to_log(deleted_resources, f"\nSERVICE {service_name} deleted because it was dependent upon escalation policy {item}, {ep_name}\n")
        conflicts_removed += 1

  elif resource == "users":
    for conflict in subscriptable['error']['conflicts']:
      conflicts += 1
      conflict_type = conflict["type"]
      conflict_id = conflict["id"]
      log.info(f"Deleting {conflict_type} {conflict_id}")
      endpoint = make_plural(conflict['type'])
      url = f"""{base_url}/{endpoint}/{conflict["id"]}"""
      # get a backup of thing being deleted
      backup = requests.request('GET', url, headers=headers)
      attempt = requests.delete(url, headers=headers)
      backup_name = get_name(conflict["type"], backup.json())
      log.info(backup_name)
      if conflict['type'] == "incident":
        # if the conflict is an open incident, resolve that incident
        attempt = resolve_incident(conflict['id'])
      # if able to delete the conflicting object or resolve the open incident,
      # record backup schema to log and write name to file that lists deleted things  
      if attempt.status_code == 200 or attempt.status_code == 204:
        write_to_log(backup_file, backup.text)
        write_to_log(deleted_resources, conflict["type"]+ " " + backup_name)
        conflicts_removed += 1
      # if attempt to delete thing or resolve incident does not work, print out the status code
      # followed by the pagerduty error messages
      if attempt.status_code > 204:
        log.error(attempt.status_code)
        attempt_subscript = attempt.json()
        for error in attempt_subscript["error"]["errors"]:
          log.error(f"ERROR: {error}")
          # record in error log that we were unable to delete the csv-named object
          error_log_msg = f"\n\nERROR: User {item} could not be deleted because of a {conflict['type']} they are associated with. Tried to remove {conflict['type']}. "
          error_log_msg += error + ": " + backup_name + "\n"
          write_to_log(error_log, error_log_msg)  

# get schedule by id to find out which escalation policies use it, then delete those ep's
  elif resource == "schedules":
    log.info("Attempting to delete escalation policies associated with schedule.")
    # get the schema of the schedule so can record to backup file later
    schedule = requests.request('GET', path, headers=headers)
    # make subscriptable so can look up the name so can add name to log that lists successfully
    # deleted things
    schedule_subscript = schedule.json()
    schedule_name = get_name(resource, schedule_subscript)
    # go through each escalation policy attached to a schedule and try to remove it
    for ep in schedule_subscript["schedule"]["escalation_policies"]:
      conflicts += 1
      url = "{}/escalation_policies/{}".format(base_url, ep['id'])
      deleted_ep = requests.request('GET', url, headers=headers)
      deleted_ep_subscript = deleted_ep.json()
      ep_id = deleted_ep_subscript["escalation_policy"]["id"]
      ep_name = get_name(deleted_ep, deleted_ep_subscript)
      attempt = requests.delete(url, headers=headers)
      if attempt.status_code == 204:
        conflicts_removed += 1
        message = f"Removed the escalation policy {ep_name} because it was preventing schedule "
        message += f"{item}, {schedule_name}, from being deleted. " 
        # add the name of the escalation policy to this list of deleted resources, plus an explanation
        # for why it was deleted, since it is not something that was explicitly named on the csv
        write_to_log(deleted_resources, message)
        # backup the escalation policy to deleted_resources file   
        write_to_log(backup_file, deleted_ep.text)
      elif attempt.status_code > 204:
        attempt_subscript = attempt.json()
        # if the attempt to remove the escalation policy is unsuccessful, print out the error 
        # from the request response
        for error in attempt_subscript["error"]["errors"]:
          log.error(f"{attempt.status_code} ERROR: {error}")
        # record to the error log which csv-named schedule was not deleted, explaining that it is being used
        # by the escalation policy (which the program was not able to delete if 400 error occurred)  
        error_log_msg = (f"\n\nUnable to delete schedule {item}, {schedule_name}, because it is being used by " 
          f"escalation policy {ep_name}, {ep_id}")
        write_to_log(error_log, error_log_msg)

  # Let the TSE know how many conflicts there were vs. how many were removed
  # This will explain why dependencies removed evaluates to true or false
  log.info(f"conflicts: {conflicts}  conflicts removed: {conflicts_removed}")
  if conflicts_removed == conflicts:
    dependencies_removed = True
  log.info("Dependencies removed: ", dependencies_removed)
  return dependencies_removed


def get_auth_token():
  """ 
  Asks for the authorization token (REST API key) and confirms that it corresponds to the correct account
  Uses pdpyras. Updates global variable `account`. 
  """
  # engineer for api auth token from account being accessed
  auth_token = getpass("API auth token")
  # borrowed from migration script
  global account
  account = APISession(auth_token)
  try:
    subdomain = account.subdomain
  except Exception as e:
    subdomain = None
  if subdomain is None:
    subdomain = 'NETWORK_ERR_OR_TOKEN_INVALID'
    log.info(subdomain)
  log.info("Entered key %s corresponds to subdomain: %s"%(account.trunc_token, subdomain))
  # if the auth token does not correspond to a valid subdomain, we
  # need to start over
  if subdomain == "NETWORK_ERR_OR_TOKEN_INVALID":
    get_auth_token()  
  # get confirmation that the associated subdomain is indeed the one
  # the TSE wants to delete things from 
  # if "is this subdomain correct" evaluates to true, update headers accordingly         
  elif do_prompt_yn(
    f"Does this subdomain {subdomain} correspond to the account from which you would like to delete resources"):
    global headers
    headers["Authorization"] = f" Token token={auth_token}"
    headers["Accept"] = "application/vnd.pagerduty+json;version=2"   
  # if it is not the right subdomain, start over  
  else:
    get_auth_token()  
  
def get_email():  
  """ valid user email attached to pd account is necessary for when incidents need to be resolved 
  in order to delete users. Updates global variable `headers`."""
  proceed_with_email = False
  while not proceed_with_email:
    # have tse enter an email 
    user_email = do_prompt_value("\nAccount user email to make requests from")
    # confirm that the email looks right
    proceed_with_email = do_prompt_yn("You entered: {} \n Is this the email you would like to proceed" 
      " with".format(user_email)) 
    log.info(proceed_with_email) 
  # update the headers
  global headers
  headers["From"] = user_email


def make_log_files():
  """
  Summary: Makes three types of files: 1. A simple list of deleted objects. Objects are listed by type and name 
  (eg. Schedule Default, User Somebody, etc.) 2. A file consisting of backup schemas of each resource that gets
  deleted, in case customer wants to restore deleted objects. 3. An error log with what I consider very readable
  errors explaining why certain objects could not be deleted. Logs are put in directory called `logs` and titled
  by name of subdomain + datetime when script was executed
  """
  # make a folder in current directory called "logs"
  logs_directory = os.getcwd() + "/logs"
  if not os.path.exists(logs_directory):
    os.mkdir(logs_directory)
  # records just the resource type and id to log file
  global deleted_resources
  deleted_resources = "logs/{}_{}_deleted_resources.txt".format(now, account.subdomain)
  with open(deleted_resources, 'a') as dr_file:
    dr_file.write("Resources deleted on {} at {}\n\n".format(date, time))
  # creates backup file in logs subdirectory and appends the schema of the deleted resource to the file (in case of mistakes or regrets, etc.)
  global backup_file
  backup_file = "logs/{}_{}_backup.txt".format(now, account.subdomain)
  with open(backup_file, 'a') as bu_file:
    bu_file.write("Backups for {} from {} at {}\n\n".format(account.subdomain, date, time))

  # creates file that deletion errors get recorded to. this will help make sense of why a particular thing
  # could not be deleted
  global error_log
  error_log = "logs/{}_{}_error_log.txt".format(now, account.subdomain)
  with open(error_log, 'a') as el_file:
    el_file.write("Errors with deleting resources from {} on {} at {}".format(account.subdomain, date, time))
  # for ease of testing
  return error_log


def main():

  get_auth_token()
  get_email()
  make_log_files()
  dependency_question = ("If a resource from the CSV can not be deleted because other resources are dependent on it "
    "(for example, an escalation policy that contanis services, or a team that is on a schedule), would you prefer to "
    "skip the resource with dependencies, or delete the other resources which are dependent on it? Select 'n' to skip "
    "resource and 'y' to delete attached dependencies")
  global delete_dependencies
  delete_dependencies = do_prompt_yn(dependency_question)
  to_delete_dict = construct_dictionary()
  delete_resource(to_delete_dict)

 
if __name__=='__main__':
  sys.exit(main())