import json
import requests
import sys

vacationing_user = "P7K46SG"
replacement_user = "P8JISOQ"

schedule_ids = ["P3N7BAC", "PRKL6HV"]

api_key = "WTS8E_CuvcyrnLHEy_JR"

since = "2017-12-15T00:00:00-04:00" # Example: 2017-12-15T00:00:00-04:00
until = "2017-12-25T00:00:00-04:00"

HEADERS = {
		"Content-Type": "application/json",
		"Authorization": "Token token={}".format(api_key),
		"Accept": "application/vnd.pagerduty+json;version=2"
	}


def find_shifts():
	"""Find all on-call shifts on the specified schedules 
	between `since` and `until`"""

	params = {
		"since": since,
		"until": until
	}

	shifts = {} # {(start, end): schedule_id}

	for schedule in schedule_ids:
		print("Getting schedule data for schedule ID: {}".format(schedule))
		
		r = requests.get("https://api.pagerduty.com/schedules/{}".format(schedule),
			headers=HEADERS,
			params=params)

		for shift in r.json()["schedule"]["final_schedule"]["rendered_schedule_entries"]:

			if shift["user"]["id"] == vacationing_user:
				print("Found shift for vacationing_user from {start} to {end}".format(start=shift["start"],
																					  end=shift["end"]))

				dates = (shift["start"], shift["end"])

				shifts[dates] = schedule

		print("Finished getting schedule data for schedule ID: {}".format(schedule))

	return shifts


def create_overrides():
	"""For shift in find_shifts(), create an override to replace vacationing_user with replacement_user."""

	shifts = find_shifts()

	for dates, schedule in shifts.iteritems():
		start, end = dates

		override_data = {
			"override": {
				"start": start,
				"end": end,
				"user": {
					"id": replacement_user,
					"type": "user_reference" 
				}
			}
		}

		print("Creating override on schedule {schedule} from {start} to {end}".format(schedule=schedule,
																					  start=start,
																					  end=end))

		r = requests.post("https://api.pagerduty.com/schedules/{}/overrides".format(schedule),
						  headers=HEADERS,
						  data=json.dumps(override_data))

		if r.status_code == 201:
			print("Successfully created override")
		else:
			print("Error creating override on schedule {schedule} from {start} to {end}".format(schedule=schedule,
																								start=start,
																								end=end))


if __name__ == "__main__":
	create_overrides()
