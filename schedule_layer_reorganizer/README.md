
# Schedule Layer Reorganizer

### Description
This script GETs a list of schedules and saves them in unique files named after
their schedule IDs, with schedule layers reversed.

GET requests for schedules show schedule layers in reverse order to PUT and POST requests,
so this script allows a user to easily GET the schedule and automatically put the schedule
layers in the correct order for a PUT or POST request.

### Usage

`python3 schedule_layer_reorganizer.py -k {API-KEY} -i {ID}`

The script can be run on multiple schedules at once.
