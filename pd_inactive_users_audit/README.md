# Inactive User Audit

Scans a PagerDuty account for schedules and escalation policies that still reference inactive (deleted) users, so stale references can be cleaned up.

## Purpose

This script helps PagerDuty administrators:

* **Find stale references** - Schedule layers or escalation rules that still point at deleted users
* **Audit schedules** - Identify on-call schedules with inactive users in their layers
* **Audit escalation policies** - Identify escalation rules that directly target inactive users
* **Clean up configuration** - Remove dead references left behind after a user was deleted

## Requirements

* Python 3.7+
* PagerDuty REST API key with read access to:
  * Schedules
  * Escalation Policies

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Console Output Only)

```bash
export PAGERDUTY_API_KEY="your-api-key"
python pd_inactive_users_audit.py
```

### Generate CSV Report

```bash
python pd_inactive_users_audit.py --csv report.csv
```

### Pass the API Key Directly

```bash
python pd_inactive_users_audit.py --api-key YOUR_API_KEY --csv report.csv
```

### EU-Region Accounts

```bash
python pd_inactive_users_audit.py --base-url https://api.eu.pagerduty.com
```

### Scan Only Schedules or Only Escalation Policies

```bash
python pd_inactive_users_audit.py --schedules-only
python pd_inactive_users_audit.py --policies-only
```

### All Options

| Option | Description |
|--------|-------------|
| `--api-key` | PagerDuty REST API key (defaults to the `PAGERDUTY_API_KEY` env var) |
| `--base-url` | Override the API base URL, e.g. `https://api.eu.pagerduty.com` for EU-region accounts |
| `--csv` | Path to write a CSV report to |
| `--schedules-only` | Only scan schedules, skip escalation policies |
| `--policies-only` | Only scan escalation policies, skip schedules |

## Output

### Console Summary

```
Scanning schedules...
Scanning escalation policies...

=== Schedules with inactive users (2 findings) ===
  [PXXXXXX] Primary On-Call  (layer: Layer 1)  -> inactive user: John Doe (deleted_at=2024-01-15T10:00:00Z)
  [PYYYYYY] Secondary On-Call  (layer: Weekend Layer)  -> inactive user: jane@example.com (deleted_at=None)

=== Escalation policies with inactive users (1 findings) ===
  [PZZZZZZ] Default Escalation Policy  (escalation rule #2)  -> inactive user: Bob Wilson (deleted_at=2024-03-01T09:30:00Z)

Total findings: 3
```

### CSV Report Fields

| Field | Description |
|-------|-------------|
| `resource_type` | `schedule` or `escalation_policy` |
| `resource_id` | PagerDuty ID of the schedule or escalation policy |
| `resource_name` | Name of the schedule or escalation policy |
| `resource_url` | HTML URL of the schedule or escalation policy |
| `context` | Schedule layer name or escalation rule number where the inactive user was found |
| `user_id` | PagerDuty ID of the inactive user, if present |
| `user_name` | Name or summary of the inactive user, if present |
| `deleted_at` | The user's `deleted_at` timestamp, if present |

## What Counts as an "Inactive User"?

A user reference is considered inactive/deleted if it carries a `deleted_at` field (regardless of value), or if its `self` link is `null`. This happens when a user has been removed from PagerDuty but a stale reference to them remains inside a schedule layer or escalation rule.

### Common Reasons for Stale References

* User was deleted without first being removed from schedules or escalation policies
* Bulk user offboarding that didn't clean up on-call configuration
* Team reorganization that left old schedule layers in place

### Exit Codes

The exit code is `0` whether or not inactive users are found; it is non-zero only on a hard error (missing/invalid API key, network error, etc.).
