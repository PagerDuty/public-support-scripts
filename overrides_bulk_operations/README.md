# Override Bulk Operation Scripts

Using `vacation_overrides.py` (originally by Lucas Epp:
[lfepp/35a2ce76114e7e6e3d7dece79eb7c635](https://gist.github.com/lfepp/35a2ce76114e7e6e3d7dece79eb7c635))
one can create overrides on all schedules where a user going on vacation would be on-call, and overrides them with another user on that schedule.

If a lot of overrides are accidentally added, or one wishes to revert that
action, these overrides can be almost as easily removed. The only way otherwise
to clean up overrides is clicking on each and every one of them after assessing
whether it is the correct override to delete, so we have scripts for that too.

To clean up overrides in an automated fashion:

1. Run `get_overrides.py`.
2. Modify the CSV file created by this script to remove any overrides that shouldn't be deleted, if any.
3. Run `mass_delete_overrides.py` on the CSV to remove the overrides.


---

# Input Key 
## `get_overrides`
Gets all overrides in a schedule and export to a CSV file. The first column of output will be the schedule ID and the second should be the override ID, and the third will be a column identifying the user and time.

- `--api-key`: "REST API key"
- `--csv-file`: "Output CSV file. Data will begin in the very first row; no column names."
- `--start`: "Start date of search"
- `--end`: "End date of search"
- `--schedules`: "IDs of schedules in which to find overrides. If unspecified, all schedules will be included."


## `vacation_overrides`
For a given user going on vacation, and another given user who will fill their shoes while away, create overrides on all the vacationing user's schedules, such that the replacement user covers all the shifts that the vacationing user will be gone.

- `--vacationer`: "Login email address of the user who is going on vacation."
- `--substitute`: "Login email address of the user who is covering the shifts of the vacationing user."
- `--api-key`: "PagerDuty REST API key to use for operations."
- `--start`: "Start date of the vacation."
- `--end`: "End date of the vacation."
- `--schedules`: "IDs of schedules in which to create overrides. If unspecified, all schedules will be included."


## `mass_delete_overrides`
Deletes overrides listed in a CSV file. The first column should be the schedule ID and the second should be the override ID. More columns can be included after the first.

- `--api-key`: "REST API key"
- `--csv-file`: "Path to input CSV file. Data should begin in the very first row; no column names."
