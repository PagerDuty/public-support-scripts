# Create / Remove Maintenance Windows in Bulk

The `create_recurring_maintenance_window.py` script will allow you to create
recurring maintenance windows. If you make a mistake, or need to remove them,
you can run the `remove_all_future_maintenance_windows.py` script to clear them
out.

Both of these scripts, per their helptext, have a `-n/--dry-run` option that
will allow you to see the changes that will be made without actually making
those changes.


#### Example usage `create_recurring_maintenance_window.py`:

```
python3 create_recurring_maintenance_windows.py \
--api-key u+zZ0ozZ0ozZ0ozZ0oZz \
--requester user@example.com \
--service P000000 \
--date 2022-07-02T04:00:00-0700 \
--description "Scheduled weekly maintenance" \
--duration 30 \
--period 168 \
--number 8
```


#### Example usage of `remove_all_future_maintenance_windows.py`:

```
python3 remove_all_future_maintenance_windows.py -k u+zZ0ozZ0ozZ0ozZ0oZz -s P000000
```