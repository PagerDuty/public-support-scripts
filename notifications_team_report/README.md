# Notifications by Team Report

Generates notification reports for each team. A work-around for how notification reports in analytics cannot yet provide a per-team drilldown nor generate the report according to the team lens.

As a note, if you have a Digital Operations account or if you've already purchased access to the *PagerDuty Analytics* product, you may find what you need in the **Team Health** report within the "Insights" portion of PD Labs:

https://support.pagerduty.com/docs/pd-labs#team-health

This python script will generate reports for each team on the account, as well as totals for the account.  


## Input Format

Running the script requires the provision of only one argument: a global REST API key (read-only is fine).

To execute the script, run this with your key and email:

```
./notifications_team_report.py -k API_KEY_HERE 
```

Several other options are available below, but are not required.

## Options

- `-k`/`--api-key`: _(required)_ REST API key (should be a global key)
- `-i`/`--interval`: _(optional)_ The number of days back in history over which to generate the report. (Default: 30)
- `-v`/`--verbose`: _(optional)_ Turn on debug level logging and progress reporting.
- `-w`/`--write-file`: _(optional)_ A file which will be used to cache data from the API prior to reporting. Helpful for large datasets.
- `-r`/`--resume-file`: _(optional)_ Read data from this previously cached file instead of the API.

