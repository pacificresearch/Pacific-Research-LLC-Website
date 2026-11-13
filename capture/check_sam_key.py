#!/usr/bin/env python3
"""Daily health check for the SAM.gov credential.

Two independent questions, because either one alone gives false comfort:

  1. Does the credential still WORK right now? (one live keyed request)
  2. How many days until it EXPIRES? (read from capture/SAM_KEY.md)

A key can be live today and dead tomorrow, so a working probe is not
evidence the pipeline is safe for the week. And a date alone is not
evidence either — a key can be revoked early. Both are reported.

Exit codes
  0  working, and more than WARN_DAYS until expiry
  1  working, but expiry is close (or the date is missing/unparseable)
  2  NOT working — the pipeline is blind right now

Run from the repository root. Needs no arguments and no key: on the
cloud environment the proxy attaches the credential. Off-proxy, set
SAM_API_KEY.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

WARN_DAYS = 14          # start nagging this far out
RECORD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SAM_KEY.md")
API = "https://api.sam.gov/opportunities/v2/search"

RENEW = (
    "  Renew (about 60 seconds):\n"
    "    1. sam.gov > Sign In > Workspace > Account Details > API Key\n"
    "       > regenerate, copy it\n"
    "    2. claude.ai/code > environment settings > Network secrets >\n"
    "       the api.sam.gov entry > replace the value\n"
    "    3. update EXPIRES: in capture/SAM_KEY.md and commit\n"
)


def expiry_days():
    """Days until the recorded expiry, or None if not recorded/parseable."""
    try:
        with open(RECORD, encoding="utf-8") as fh:
            m = re.search(r"EXPIRES:\s*(\d{4}-\d{2}-\d{2})", fh.read())
    except OSError:
        return None, None
    if not m:
        return None, None
    try:
        when = dt.date.fromisoformat(m.group(1))
    except ValueError:
        return None, None
    return (when - dt.date.today()).days, when


def probe():
    """Return (ok, detail). Sends no key: the proxy supplies it."""
    today = dt.date.today()
    params = {
        "postedFrom": (today - dt.timedelta(days=2)).strftime("%m/%d/%Y"),
        "postedTo": today.strftime("%m/%d/%Y"),
        "limit": 1,
        "ncode": "541715",
    }
    key = os.environ.get("SAM_API_KEY", "")
    if key:                      # off-proxy fallback
        params["api_key"] = key
    try:
        with urllib.request.urlopen(
                API + "?" + urllib.parse.urlencode(params), timeout=60) as r:
            json.loads(r.read())
            return True, "HTTP %d" % r.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if exc.code in (401, 403) or "API_KEY_INVALID" in body:
            return False, "HTTP %d — key rejected" % exc.code
        if exc.code == 404 and not key:
            return False, "HTTP 404 — no credential reached SAM"
        if exc.code == 429:
            # Quota exhaustion is NOT a dead key: the credential authenticated
            # fine, it has simply spent its daily allowance (usually because a
            # sweep already ran today). Reporting it as dead sends Andrew to
            # regenerate a key that is working, and the real key keeps its
            # expiry. SAM names the reset time in the body.
            when = ""
            m = re.search(r"access API after ([0-9A-Za-z:+\- ]+)", body or "")
            if m:
                when = " — resets %s" % m.group(1).strip()
            return "quota", "HTTP 429 — daily quota spent%s" % when
        return False, "HTTP %d" % exc.code
    except Exception as exc:                                  # noqa: BLE001
        # A network blip is not a dead key. Say so rather than crying wolf.
        return None, "%s: %s" % (type(exc).__name__, str(exc)[:120])


def main():
    ok, detail = probe()
    days, when = expiry_days()

    if ok == "quota":
        print("SAM key is VALID but THROTTLED (%s)." % detail)
        print("  The credential authenticated — it has spent today's request")
        print("  allowance, almost always because a sweep already ran today.")
        print("  Do NOT regenerate the key: that does not add quota and the")
        print("  current key is fine. Re-run after the reset shown above.")
        if days is not None and when is not None:
            print("  Recorded expiry: %s (%d days)." % (when, days))
        return 1

    if ok is None:
        print("SAM key check INCONCLUSIVE — could not reach SAM (%s)." % detail)
        print("  This is a network problem, not necessarily a dead key.")
        return 1

    if not ok:
        print("SAM CREDENTIAL IS DEAD (%s)." % detail)
        print("  Every capture run is blind until this is fixed. Runs abort")
        print("  with exit 2 and write nothing, so no blank report is made.\n")
        sys.stdout.write(RENEW)
        return 2

    if days is None:
        print("SAM key WORKS (%s), but no usable EXPIRES: date is recorded" % detail)
        print("  in capture/SAM_KEY.md, so there is no advance warning. Add one.")
        return 1

    if days < 0:
        print("SAM key still works (%s) but its recorded expiry (%s) has"
              % (detail, when))
        print("  PASSED. Either it was renewed and the date was not updated,")
        print("  or it is about to stop. Resolve it now.\n")
        sys.stdout.write(RENEW)
        return 1

    if days <= WARN_DAYS:
        print("SAM key works (%s) but EXPIRES IN %d DAY%s (%s)."
              % (detail, days, "" if days == 1 else "S", when))
        print("  Renew before then or the pipeline goes dark.\n")
        sys.stdout.write(RENEW)
        return 1

    print("SAM key OK (%s). %d days until expiry (%s)." % (detail, days, when))
    return 0


if __name__ == "__main__":
    sys.exit(main())
