#!/usr/bin/env python

# PagerDuty Support asset: update_user_emails,fix_emails

import argparse
import csv
import pprint
import re
import sys

import pdpyras

session = None


def apply_replacement_logic(args, email):
    """Returns the new email address according to replacement options."""
    regex_replace = True
    find = args.find_pattern
    if args.find_pattern is None:
        find = args.query
        regex_replace = False
    repl = args.replacement_pattern
    if regex_replace:
        to_email = re.sub(find, repl, email)
    else:
        to_email = email.replace(find, repl)
    return to_email


def update_email(user, new_email):
    """
    Update a user's email address.

    :param user: Dictionary representation of the user
    :param new_email: New email address that the user shall have
    """
    global session
    try:
        self_url = f"https://api.pagerduty.com/users/{user['id']}"
        session.rput(self_url, json={"type": "user", "email": new_email})
    except pdpyras.PDClientError as e:
        if e.response is not None:
            print(
                "Failed to update user; HTTP %d: %s"
                % (e.response.status_code, e.response.text)
            )
        else:
            raise e


def update_contact_method(user, cm, new_email):
    """
    Updates an email contact method.

    :param cm: Dictionary representation of the contact method
    :param new_email: New email address of the contact method
    """
    try:
        self_url = (
            f"https://api.pagerduty.com/users/{user['id']}/contact_methods/{cm['id']}"
        )
        session.rput(
            self_url, json={"type": "email_contact_method", "address": new_email}
        )
    except pdpyras.PDClientError as e:
        if e.response:
            print(
                "\tCouldn't update contact method; HTTP %d: %s"
                % (e.response.status_code, e.response.text)
            )


def get_user_email_changes(args):
    """
    Retrieves users to be updated.

    :param args: Arguments namespace
    :yields: A 2-tuple containing a dictionary representation of the user
        dictionary object in position 0 and the new email address in position 1.
    """
    global session
    if args.csv_file:
        # Derive find/replace list from CSV file
        reader = csv.reader(args.csv_file)
        for row in reader:
            from_email, to_email = tuple(map(lambda s: s.strip(), row))
            user = session.find(
                "users",
                from_email,
                attribute="email",
                params={"include[]": ["contact_methods"]},
            )
            if not user:
                print("No user found with matching email: " + from_email)
                continue
            yield (user, to_email)
    else:
        # Derive find/replace list from dynamic query/regex
        kw = {}
        if not args.no_contact_methods:
            kw["params"] = {"include[]": ["contact_methods"]}
        if args.query:
            kw.setdefault("params", {})
            kw["params"]["query"] = args.query
        for user in session.iter_all("users", **kw):
            if args.query and not args.query in user["email"]:
                # Email doesn't match but maybe some of their name did
                continue
            to_email = apply_replacement_logic(args, user["email"])
            yield (user, to_email)


def replace_emails(args):
    global session
    for user, new_email in get_user_email_changes(args):
        print("User ID=%s (%s):" % (user["id"], user["summary"]))
        if user["email"] != new_email:
            print("\tUpdating email: %s -> %s" % (user["email"], new_email))
            if not args.dry_run:
                update_email(user, new_email)
        else:
            print("\tNo change in login email.")
        if not args.no_contact_methods:
            for cm in user["contact_methods"]:
                # It must be an email contact method, and it must either match
                # the user's profile email or this must be a dynamic, all-users
                # non-CSV global find-and-replace (in which case we permit the
                # same replacement pattern from being applied to the contact
                # method, even if the replacement operation is different for the
                # contact method than for the profile email)
                if cm["type"] == "email_contact_method":
                    if cm["address"] == user["email"]:
                        # Use the new value from the CSV
                        new_cm_address = new_email
                    elif not args.csv_file:
                        # Use the globally applicable find/replace logic
                        new_cm_address = apply_replacement_logic(args, cm["address"])
                    else:
                        # Skip because it's not the address we want to replace
                        # (because the addresses to replace are specified via
                        # CSV file and this isn't one of them):
                        continue
                    if cm["address"] != new_cm_address:
                        print(
                            "\tUpdating contact method %s: %s to %s"
                            % (cm["id"], cm["address"], new_email)
                        )
                        if not args.dry_run:
                            update_contact_method(user, cm, new_cm_address)


def main():
    global session
    ap = argparse.ArgumentParser(
        description="Mass-update email addresses of " "users in a PagerDuty account."
    )
    ap.add_argument("-k", "--api-key", required=True, help="API key")
    # "CSV",
    # description="CSV-based update: users to update and how to make the "
    # "update is specified in a CSV file",
    # "Query",
    # description="Query-based update: users to update given by a query and "
    # "replacement pattern"
    query_or_csv_group = ap.add_mutually_exclusive_group(required=True)
    query_or_csv_group.add_argument(
        "-f",
        "--csv-file",
        default=None,
        type=argparse.FileType("r"),
        help="CSV file specifying users to update "
        "and their new email addresses. Must have two columns: the first is "
        "the login email of the user, and the second is the email address to "
        "which it should be changed. Input is expected to start at the first "
        "line; there should be no column titles row.",
    )
    query_or_csv_group.add_argument(
        "-q",
        "--query",
        type=str,
        help="Query to use for matching users to be updated. The query is run "
        "against the users' login emails.",
    )
    query_or_csv_group.add_argument(
        "-a",
        "--all-users",
        action="store_true",
        default=False,
        help="Perform replacement over all users.",
    )
    ap.add_argument(
        "-e",
        "--find",
        dest="find_pattern",
        default=None,
        help="Regex to match in the email addresses. If this is unspecified "
        "and -q is given, the query itself will be used as the search pattern, "
        "and a plain text find/replace will be performed instead of regex.",
    )
    ap.add_argument(
        "-r",
        "--replace",
        dest="replacement_pattern",
        default=None,
        help="Replacement pattern to use for emails.",
    )
    ap.add_argument(
        "-n",
        "--dry-run",
        default=False,
        action="store_true",
        help="Don't actually make changes, but print out each change that "
        "would be made.",
    )
    ap.add_argument(
        "-o",
        "--no-contact-methods",
        default=False,
        action="store_true",
        help="Do not update email contact methods as well "
        "as login email addresses. By default this is False and contact "
        "methods will be included.",
    )
    args = ap.parse_args()
    if (
        args.all_users
        and None in (args.find_pattern, args.replacement_pattern)
        or (args.query and args.replacement_pattern is None)
    ):
        print(
            "There is insufficient information to determine what you want to "
            "do.\n- If using the --all-users option, you must also provide "
            "--find and --replace to specify how the emails should "
            "be updated\n- If using --query, you must at least provide "
            "--replace"
        )
        return
    session = pdpyras.APISession(args.api_key)
    replace_emails(args)


if __name__ == "__main__":
    main()
