## Delete Multiple Object Types with CSV

#### Disclaimer: While PagerDuty Support is responsible for maintaining this script, we are not responsible for how it is used. The purpose of this script is to permanently delete items from your account, so please use it wisely. 

#### Before running the script, you need the following:

**1**. a CSV formatted this way:
	
		PJLCSCH, teams
		PDQU0LB, services
		PDKSVHE, escalation_policies
		

  i.e., the id of an object, followed by a comma, followed by the pluralized name of the object **type**

 - order is irrelevent 
 - name of object type must be pluralized

**2**. An understanding on how to handle dependencies.

 Because PagerDuty object types reference one another, when you attempt to delete a given object, a conflict will arise if another object depends on it. The order in which objects are deleted in the script should reduce such conflicts. However, the most optimal order can only reduce these conflicts - not avoid them completely. For this reason, an understanding with your team, manager, admin, and/or account owner should be established beforehand on how to handle these conflicts. There are two options for how the script can behave when it gets to a csv-named object with dependencies.
	
   1. It can leave the object alone
   2. It can delete the objects depending on the csv-named 
object, and then delete the csv-named object

 In the case of the latter option, dependency deletion will only apply to one degree of separation from the csv-named object. For example, if running the script with the delete_dependencies set to True, and there is a schedule on the csv that contains an escalation policy, the script will attempt to delete that escalation policy. *But*, if that escalation policy is being used by a service, the script will leave both the service and the escalation policy in place. In this example, this would have to be a service that is not included in the csv, as services are deleted first to avoid exactly these types of dependency issues.

**3**. A REST API token for the account

#### What to provide during execution of the script:

1. a REST API auth token
2. a user email associated with account
3. A boolean value for delete_dependencies (explained above)

to run the script: `ptyhon delete_features_with_csv.py name_of_csv.csv`


#### What the script produces:

The script creates a folder called logs, and in this folder creates three text files, the names of which all start with the date, time, and name of subdomain. This will look roughly like:
     `2-6-10:12_isabella_backup.txt`

All the scripts will be divided into five sections, which look like this:

>
>---services---
>
>---escalation_policies---
>
>---schedules---
>
>---teams---
>
>---users---



The three types of text files produced by the script are:
  
1. Using the names of specific objects, a simple list of what got deleted.
2. A backup of everything that got deleted. The backups are GET request responses of the object.
3. Errors that occurred when trying to delete certain objects. If no errors occurred, this file will look like the above block quote (just object type sections). Errors will have very readable explanations for straightforward conflicts, such as "Unable to delete schedule P0CTUZ1, Default, because can't delete an escalation policy that contains services.
Attached Escalation Policy: Default, PAW33P9". Errors that could have a variety of causes will contain the JSON response from the delete request. 

