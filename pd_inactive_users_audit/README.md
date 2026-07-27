# Inactive User Audit

Scans a PagerDuty account for schedules, shift-based (v3) schedules, and escalation policies that still reference inactive (deleted) users, so stale references can be cleaned up.

## Purpose

This script helps PagerDuty administrators:

* **Find stale references** - Schedule layers, shift-based schedule rotations, or escalation rules that still point at deleted users
* **Audit schedules** - Identify on-call schedules (both classic and shift-based/v3) with inactive users
* **Audit escalation policies** - Identify escalation rules that directly target inactive users
* **Clean up configuration** - Remove dead references left behind after a user was deleted

## Requirements

* Python 3.10+
* PagerDuty REST API key with read access to:
  * Schedules
  * Escalation Policies
* If your account uses shift-based (v3) schedules, that API is early access; the script sends the required `X-Early-Access` header automatically. If the feature isn't enabled on your account, the v3 scan is skipped without error.

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
| `--schedules-only` | Only scan schedules (both classic and shift-based/v3), skip escalation policies |
| `--policies-only` | Only scan escalation policies, skip schedules |

## Output

### Console Summary

```
Scanning schedules...
Scanning shift-based (v3) schedules...
Scanning escalation policies...

=== Schedules with inactive users (2 findings) ===
  [PXXXXXX] Primary On-Call  (layer: Layer 1)  -> inactive user: John Doe (deleted_at=2024-01-15T10:00:00Z)
  [PYYYYYY] Secondary On-Call  (layer: Weekend Layer)  -> inactive user: jane@example.com (deleted_at=None)

=== Shift-based (v3) schedules with inactive users (1 findings) ===
  [PWWWWWW] Follow-the-Sun Rotation  (rotation event: Day Shift)  -> inactive user: PUUUUUU (deleted_at=2024-07-23T02:01:30Z)

=== Escalation policies with inactive users (1 findings) ===
  [PZZZZZZ] Default Escalation Policy  (escalation rule #2)  -> inactive user: Bob Wilson (deleted_at=2024-03-01T09:30:00Z)

Total findings: 4
```

### CSV Report Fields

| Field | Description |
|-------|-------------|
| `resource_type` | `schedule`, `schedule_v3`, or `escalation_policy` |
| `resource_id` | PagerDuty ID of the schedule or escalation policy |
| `resource_name` | Name of the schedule or escalation policy |
| `resource_url` | HTML URL of the schedule or escalation policy |
| `context` | Schedule layer name, rotation event name (v3), or escalation rule number where the inactive user was found |
| `user_id` | PagerDuty ID of the inactive user, if present |
| `user_name` | Name or summary of the inactive user, if present (not available for v3 schedule findings - see below) |
| `deleted_at` | The user's `deleted_at` timestamp, if present |

## What Counts as an "Inactive User"?

For classic schedules and escalation policies, a user reference is considered inactive/deleted if it carries a `deleted_at` field (regardless of value), or if its `self` link is `null`. This happens when a user has been removed from PagerDuty but a stale reference to them remains inside a schedule layer or escalation rule.

Shift-based (v3) schedule rotation events assign users as `user_member` entries that only ever carry a `type` and `user_id` - there's no `self` link or name/summary to inspect - so a `user_member` is flagged as inactive purely on the presence of a `deleted_at` field, e.g.:

```json
{
  "deleted_at": "YYYY-MM-DDT00:00:00Z",
  "type": "user_member",
  "user_id": "PUUUUUU"
}
```

### Common Reasons for Stale References

* User was deleted without first being removed from schedules or escalation policies
* Bulk user offboarding that didn't clean up on-call configuration
* Team reorganization that left old schedule layers or rotations in place

### Exit Codes

The exit code is `0` whether or not inactive users are found; it is non-zero only on a hard error (missing/invalid API key, network error, etc.).
