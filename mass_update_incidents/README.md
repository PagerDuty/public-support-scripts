# Mass Update Incidents

Performs status updates (acknowledge or resolve) in bulk to an almost arbitrary
number (maximum: 10k at a time) of incidents that all have an assignee user or
service (or both) in commmon. 

If operating on more than 10k incidents: it is recommended that you run the
script several times by constraining it to a service ID each time, and/or
requesting a time range by setting the `-d/--date-range` option.
