# User Association Report

Generates a report of PagerDuty users and their associations with schedules, escalation policies, teams, and open incidents. Identifies "orphan" users who are not associated with any operational resources.

## Purpose

This script helps PagerDuty administrators:

* **Identify orphan users** - Users not in any schedule, escalation policy, or team
* **Audit user associations** - See which resources each user is associated with
* **Optimize license usage** - Find unused accounts that can be removed
* **Prepare for offboarding** - Identify users with open incidents before deletion
* **Maintain security hygiene** - Discover stale accounts that shouldn't have access

## Requirements

* Python 3.6+
* PagerDuty REST API token with read access to:
  * Users
  * Schedules
  * Escalation Policies
  * Teams
  * Incidents

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Console Output Only)

```bash
python orphan_user_report.py \
  --access-token YOUR_API_TOKEN
```

### Generate CSV Report

```bash
python orphan_user_report.py \
  --access-token YOUR_API_TOKEN \
  --csv
```

### Generate JSON Report

```bash
python orphan_user_report.py \
  --access-token YOUR_API_TOKEN \
  --json
```

### Full Report (All Users with Association Flags)

By default, the script only reports orphan users. Use `--full-report` to include all users:

```bash
python orphan_user_report.py \
  --access-token YOUR_API_TOKEN \
  --full-report \
  --csv
```

### All Options

| Option | Short | Description |
|--------|-------|-------------|
| `--access-token` | `-a` | PagerDuty REST API access token (required) |
| `--csv` | `-c` | Generate CSV report |
| `--json` | `-j` | Generate JSON report |
| `--full-report` | `-r` | Include all users, not just orphans |
| `--output-dir` | `-o` | Output directory for reports (default: `reports`) |
| `--verbose` | `-v` | Verbose output (show progress) |

## Output

### Console Summary

```
============================================================
PAGERDUTY USER ASSOCIATION REPORT
============================================================
Total Users:                    150
Users in Schedules:             45
Users in Escalation Policies:   52
Users in Teams:                 120
------------------------------------------------------------
Users with Open Incidents:      8
Total Open Incidents:           23
------------------------------------------------------------
Orphan Users (no associations): 12
Orphans with Open Incidents:    2
============================================================

ORPHAN USERS WITH OPEN INCIDENTS (Action Required):
------------------------------------------------------------
  - John Doe <john@example.com> [user] - 3 open incident(s)
  - Jane Smith <jane@example.com> [user] - 1 open incident(s)

Orphan Users (no open incidents):
------------------------------------------------------------
  - Bob Wilson <bob@example.com> [limited_user]
  - Alice Brown <alice@example.com> [user]
```

### CSV Report Fields

| Field | Description |
|-------|-------------|
| `id` | PagerDuty user ID |
| `name` | User's full name |
| `email` | User's email address |
| `role` | User's PagerDuty role |
| `job_title` | User's job title |
| `time_zone` | User's time zone |
| `in_schedules` | Whether user is in any schedule |
| `in_escalation_policies` | Whether user is in any escalation policy |
| `in_teams` | Whether user is a member of any team |
| `has_open_incidents` | Whether user has open incidents assigned |
| `open_incident_count` | Number of open incidents assigned |
| `is_orphan` | Whether user is an orphan (no associations) |

### Generated Files

| File | Location |
|------|----------|
| CSV Report | `reports/orphan_users_YYYYMMDD_HHMMSS.csv` |
| JSON Report | `reports/orphan_users_YYYYMMDD_HHMMSS.json` |
| Log File | `logs/orphan_report_YYYYMMDD_HHMMSS.log` |

## What is an "Orphan User"?

An orphan user is a PagerDuty user who is **not associated with any operational resources**:

* Not on any **schedule** (no on-call rotations)
* Not a target in any **escalation policy** (won't receive escalations)
* Not a member of any **team**

These users will never receive incident notifications and may be candidates for removal.

### Common Reasons for Orphan Users

* Employee left but account wasn't deleted
* Role change to non-operational position
* Incomplete onboarding (account created but never assigned)
* Team reorganization

### Important Note

Orphan users may still have **open incidents assigned** from before they were removed from resources. The script flags these users separately — their incidents must be resolved or reassigned before the user can be safely deleted.

## Caching

The script uses caching to minimize API calls when processing large accounts:

* Users, schedules, escalation policies, and teams are fetched once
* Team membership is cached per team
* Open incidents are fetched once and indexed by assignee

This makes the script efficient even for accounts with hundreds of users and schedules.

## Changes from Previous Version

* **Removed `--from-email` requirement** - This parameter is no longer needed as the script only performs GET requests
* **Updated to use `pagerduty` package** - Migrated from deprecated `pdpyras` to the actively maintained `pagerduty` package

## Related Scripts

* [user_deprovision](../user_deprovision) - Delete users and remove them from all resources