# Create / Remove Maintenance Windows in Bulk

The `create_recurring_maintenance_window.py` script will allow you to create
recurring maintenance windows. If you make a mistake, or need to remove them,
you can run the `remove_all_future_maintenance_windows.py` script to clear them
out.

Both of these scripts, per their helptext, have a `-n/--dry-run` option that
will allow you to see the changes that will be made without actually making
those changes.
