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
