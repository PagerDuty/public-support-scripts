# Mass Update Incidents

Performs status updates (acknowledge or resolve) in bulk to an almost arbitrary
number (maximum: 10k at a time) of incidents that all have an assignee user or
service (or both) in commmon.

If operating on more than 10k incidents: it is recommended that you run the
script several times by constraining it to a service ID each time.

Alternatively, specify a time range by setting the `-d/--date-range` option. If
the difference between the beginning and end times is longer than 1 hour, the
script will run in batches of 1 hour across the time range. This is intended
to help keep each batch size within 10k incidents.

Errors returned by the REST API are reported to stderr but do not interrupt the
script's execution, to ensure that all incidents in scope are tried at least
once each.
