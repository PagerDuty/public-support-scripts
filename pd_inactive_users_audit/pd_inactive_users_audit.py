#!/usr/bin/env python3
"""
pd_inactive_user_audit.py

Scans a PagerDuty account for:
  1. Schedules whose schedule layers still reference inactive (deleted) users
  2. Escalation policies that directly target inactive (deleted) users
  3. Shift-based (v3) schedules whose rotation events still assign inactive
     (deleted) users

"Inactive" here means the user object embedded in the response either:
  - has a "deleted_at" field present (regardless of value), or
  - has "self" == null

This happens when a user has been removed from PagerDuty but still shows up
as a stale reference inside a schedule layer or escalation rule.

Shift-based (v3) schedules don't expose their rotation/event/user data on the
list endpoint (GET /v3/schedules only returns id/type/summary), so those must
be scanned one at a time via GET /v3/schedules/{id}. Deleted users show up as
a "deleted_at" field on the "user_member" entries under
rotations[].events[].assignment_strategy.members[], e.g.:

    {
      "deleted_at": "2026-07-23T02:01:30Z",
      "type": "user_member",
      "user_id": "PXXXXXX"
    }

The v3 Schedules API is early access and requires the
"X-Early-Access: flexible-schedules-early-access" header on every request.

Requires the official `pagerduty` client library:
    pip install pagerduty

Usage:
    export PAGERDUTY_API_KEY="your-api-key"
    python pd_inactive_user_audit.py
    python pd_inactive_user_audit.py --csv report.csv
    python pd_inactive_user_audit.py --api-key XXXX --csv report.csv --base-url https://api.eu.pagerduty.com

Exit code is 0 whether or not inactive users are found; it is non-zero only
on a hard error (auth failure, network error, etc.).
"""

import argparse
import csv
import os
import sys
from typing import Any, Dict, Iterable, List, Optional

try:
    import pagerduty
except ImportError:
    sys.stderr.write(
        "The 'pagerduty' package is required. Install it with:\n"
        "    pip install pagerduty\n"
    )
    sys.exit(1)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def is_inactive_user(user_obj: Optional[Dict[str, Any]]) -> bool:
    """
    A user reference is considered inactive/deleted if it carries a
    'deleted_at' field or additionally for v2 schedules if its 'self' link is null. 
    Active users don't have a 'deleted_at' field.
    """
    if not user_obj:
        return False
    if "deleted_at" in user_obj:
        return True
    if user_obj.get("self") is None:
        return True
    return False


def extract_user_ref(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Schedule-layer 'users' entries are normally shaped like:
        {"user": {...user reference...}, "member_order": 1}
    but defend against a bare user-reference dict too, just in case.
    """
    if "user" in entry and isinstance(entry["user"], dict):
        return entry["user"]
    if "id" in entry or "self" in entry or "deleted_at" in entry:
        return entry
    return None


def user_label(user_obj: Dict[str, Any]) -> str:
    return user_obj.get("summary") or user_obj.get("name") or user_obj.get("id") or "unknown"


# --------------------------------------------------------------------------
# Schedules
# --------------------------------------------------------------------------

def scan_schedules(client: "pagerduty.RestApiV2Client") -> List[Dict[str, Any]]:
    """
    GET /schedules with include[]=schedule_layers, total=true, limit=100,
    paginated via offset (handled automatically by iter_all).
    Returns a flat list of finding rows.
    """
    findings = []
    params = {
        "include[]": "schedule_layers",
        "total": True,
        "limit": 100,
    }

    for schedule in client.iter_all("schedules", params=params):
        schedule_id = schedule.get("id")
        schedule_name = schedule.get("name")
        schedule_url = schedule.get("html_url")

        for layer in schedule.get("schedule_layers", []) or []:
            layer_name = layer.get("name") or layer.get("id") or "unnamed layer"

            for entry in layer.get("users", []) or []:
                user_obj = extract_user_ref(entry)
                if user_obj is None:
                    continue
                if is_inactive_user(user_obj):
                    findings.append({
                        "resource_type": "schedule",
                        "resource_id": schedule_id,
                        "resource_name": schedule_name,
                        "resource_url": schedule_url,
                        "context": f"layer: {layer_name}",
                        "user_id": user_obj.get("id"),
                        "user_name": user_obj.get("summary") or user_obj.get("name"),
                        "deleted_at": user_obj.get("deleted_at"),
                    })

    return findings


# --------------------------------------------------------------------------
# Escalation Policies
# --------------------------------------------------------------------------

def scan_escalation_policies(client: "pagerduty.RestApiV2Client") -> List[Dict[str, Any]]:
    """
    GET /escalation_policies with include[]=targets, paginated automatically.
    Looks at each escalation_rule's targets list for directly-assigned
    user_reference targets that are inactive/deleted.
    """
    findings = []
    params = {
        "include[]": "targets",
        "total": True,
        "limit": 100,
    }

    for policy in client.iter_all("escalation_policies", params=params):
        policy_id = policy.get("id")
        policy_name = policy.get("name")
        policy_url = policy.get("html_url")

        for idx, rule in enumerate(policy.get("escalation_rules", []) or [], start=1):
            for target in rule.get("targets", []) or []:
                if target.get("type") not in ("user", "user_reference"):
                    continue  # skip schedule targets etc. - only direct user assignments
                if is_inactive_user(target):
                    findings.append({
                        "resource_type": "escalation_policy",
                        "resource_id": policy_id,
                        "resource_name": policy_name,
                        "resource_url": policy_url,
                        "context": f"escalation rule #{idx}",
                        "user_id": target.get("id"),
                        "user_name": target.get("summary") or target.get("name"),
                        "deleted_at": target.get("deleted_at"),
                    })

    return findings


# --------------------------------------------------------------------------
# Shift-based (v3) Schedules
# --------------------------------------------------------------------------

V3_SCHEDULE_HEADERS = {
    "Accept": "application/json",
    "X-Early-Access": "flexible-schedules-early-access",
}


def list_v3_schedule_refs(client: "pagerduty.RestApiV2Client") -> List[Dict[str, Any]]:
    """
    GET /v3/schedules, paginated via limit/offset/more (classic pagination).
    Each entry is just an id/type/summary reference - no rotation or user
    data is included on the list endpoint.
    """
    refs: List[Dict[str, Any]] = []
    params = {"limit": 100, "offset": 0}

    while True:
        resp = client.get("/v3/schedules", params=params, headers=V3_SCHEDULE_HEADERS)
        if not resp.ok:
            raise pagerduty.HttpError(
                f"Error listing v3 schedules: HTTP {resp.status_code}: {resp.text}",
                resp,
            )
        data = resp.json()
        refs.extend(data.get("schedules", []) or [])
        if not data.get("more"):
            break
        params["offset"] += params["limit"]

    return refs


def scan_v3_schedules(client: "pagerduty.RestApiV2Client") -> List[Dict[str, Any]]:
    """
    For each v3 schedule reference, GET /v3/schedules/{id} and look for
    inactive (deleted) users among the "user_member" entries in each
    rotation event's assignment_strategy.members.
    """
    findings = []

    try:
        refs = list_v3_schedule_refs(client)
    except pagerduty.HttpError as e:
        status = e.response.status_code if e.response is not None else None
        if status in (404, 501):
            # v3 (shift-based) schedules aren't available on this account.
            return findings
        raise

    for ref in refs:
        schedule_id = ref.get("id")
        resp = client.get(f"/v3/schedules/{schedule_id}", headers=V3_SCHEDULE_HEADERS)
        if not resp.ok:
            sys.stderr.write(
                f"Warning: could not fetch v3 schedule {schedule_id}: "
                f"HTTP {resp.status_code}\n"
            )
            continue

        schedule = resp.json().get("schedule", {}) or {}
        schedule_name = schedule.get("name")
        schedule_url = schedule.get("html_url")

        for rotation in schedule.get("rotations", []) or []:
            for event in rotation.get("events", []) or []:
                event_name = event.get("name") or event.get("id") or "unnamed event"
                strategy = event.get("assignment_strategy", {}) or {}

                for member in strategy.get("members", []) or []:
                    if member.get("type") != "user_member":
                        continue
                    # Unlike v2 user objects, v3 members never carry a "self"
                    # link at all, so the presence of "deleted_at" is the only
                    # reliable signal here (is_inactive_user()'s "self is None"
                    # check would misfire on every member).
                    if "deleted_at" not in member:
                        continue
                    findings.append({
                        "resource_type": "schedule_v3",
                        "resource_id": schedule_id,
                        "resource_name": schedule_name,
                        "resource_url": schedule_url,
                        "context": f"rotation event: {event_name}",
                        "user_id": member.get("user_id"),
                        "user_name": None,
                        "deleted_at": member.get("deleted_at"),
                    })

    return findings


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

FIELDNAMES = [
    "resource_type",
    "resource_id",
    "resource_name",
    "resource_url",
    "context",
    "user_id",
    "user_name",
    "deleted_at",
]


def print_report(findings: List[Dict[str, Any]]) -> None:
    if not findings:
        print("No inactive users found on any schedule or escalation policy.")
        return

    schedules = [f for f in findings if f["resource_type"] == "schedule"]
    v3_schedules = [f for f in findings if f["resource_type"] == "schedule_v3"]
    policies = [f for f in findings if f["resource_type"] == "escalation_policy"]

    if schedules:
        print(f"\n=== Schedules with inactive users ({len(schedules)} findings) ===")
        for f in schedules:
            print(f"  [{f['resource_id']}] {f['resource_name']}  ({f['context']})"
                  f"  -> inactive user: {f['user_name'] or f['user_id']} "
                  f"(deleted_at={f['deleted_at']})")

    if v3_schedules:
        print(f"\n=== Shift-based (v3) schedules with inactive users ({len(v3_schedules)} findings) ===")
        for f in v3_schedules:
            print(f"  [{f['resource_id']}] {f['resource_name']}  ({f['context']})"
                  f"  -> inactive user: {f['user_name'] or f['user_id']} "
                  f"(deleted_at={f['deleted_at']})")

    if policies:
        print(f"\n=== Escalation policies with inactive users ({len(policies)} findings) ===")
        for f in policies:
            print(f"  [{f['resource_id']}] {f['resource_name']}  ({f['context']})"
                  f"  -> inactive user: {f['user_name'] or f['user_id']} "
                  f"(deleted_at={f['deleted_at']})")

    print(f"\nTotal findings: {len(findings)}")


def write_csv(findings: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in findings:
            writer.writerow(row)
    print(f"\nCSV report written to: {path}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report on PagerDuty escalation policies and schedules that "
                     "reference inactive (deleted) users."
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("PAGERDUTY_API_KEY"),
        help="PagerDuty REST API key. Defaults to the PAGERDUTY_API_KEY env var.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override the API base URL, e.g. https://api.eu.pagerduty.com "
             "for EU-region accounts.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help="If provided, write results to this CSV file path.",
    )
    parser.add_argument(
        "--schedules-only",
        action="store_true",
        help="Only scan schedules (both classic and shift-based/v3), "
             "skip escalation policies.",
    )
    parser.add_argument(
        "--policies-only",
        action="store_true",
        help="Only scan escalation policies, skip schedules.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.api_key:
        sys.stderr.write(
            "No API key provided. Set PAGERDUTY_API_KEY or pass --api-key.\n"
        )
        sys.exit(1)

    client = pagerduty.RestApiV2Client(args.api_key)
    if args.base_url:
        client.url = args.base_url

    findings: List[Dict[str, Any]] = []

    try:
        if not args.policies_only:
            print("Scanning schedules...")
            findings.extend(scan_schedules(client))

            print("Scanning shift-based (v3) schedules...")
            findings.extend(scan_v3_schedules(client))

        if not args.schedules_only:
            print("Scanning escalation policies...")
            findings.extend(scan_escalation_policies(client))

    except pagerduty.HttpError as e:
        sys.stderr.write(f"PagerDuty API error: {e}\n")
        if e.response is not None:
            sys.stderr.write(f"Status: {e.response.status_code}, Body: {e.response.text}\n")
        sys.exit(2)
    except pagerduty.Error as e:
        sys.stderr.write(f"PagerDuty client error: {e}\n")
        sys.exit(2)

    print_report(findings)

    if args.csv_path:
        write_csv(findings, args.csv_path)


if __name__ == "__main__":
    main()
