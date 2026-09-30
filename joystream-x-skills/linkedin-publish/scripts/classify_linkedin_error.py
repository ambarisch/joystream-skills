#!/usr/bin/env python3
"""
Map a raw error from the LinkedIn posting tool to a stable error code, so
callers can branch on a code instead of interpreting free-form error text.

Usage:
  python3 classify_linkedin_error.py --error "429 Too Many Requests"
  echo "<raw error text or JSON>" | python3 classify_linkedin_error.py

Prints JSON: {"error_code": "RATE_LIMIT", "retryable": true, "message": "..."}

Codes (checked in this order, first match wins):
  DUPLICATE        LinkedIn rejected identical recent content
  RATE_LIMIT       429 / throttled / daily or application limit / 402 payment
  AUTH             401, missing/expired/revoked token, connector not connected
  FORBIDDEN        403 for any other reason (missing permission, restricted)
  TOO_LONG         LinkedIn itself rejected the length
  UNKNOWN_OUTCOME  timeout, connection dropped, 5xx: the post MAY have gone out
  OTHER            anything else

NO_TOOL is never produced here: the skill raises it itself when no posting
tool exists.
"""
import argparse
import json
import re
import sys

RULES = [
    ("DUPLICATE", False, [r"duplicate"]),
    ("RATE_LIMIT", True, [r"\b429\b", r"too many requests", r"rate.?limit",
                          r"throttl", r"daily.{0,20}limit", r"quota",
                          r"usage.?cap", r"\b402\b", r"payment required"]),
    ("AUTH", False, [r"\b401\b", r"unauthori[sz]ed", r"not authenticated",
                     r"authenticat", r"invalid.{0,20}token", r"expired.{0,20}token",
                     r"token.{0,20}(expired|revoked|invalid)", r"revoked",
                     r"credential", r"not connected", r"reconnect", r"oauth"]),
    ("FORBIDDEN", False, [r"\b403\b", r"forbidden", r"not permitted",
                          r"not allowed", r"not enough permissions",
                          r"access denied", r"restricted", r"suspended"]),
    ("TOO_LONG", False, [r"too long", r"exceeds?.{0,30}(length|characters|3000)",
                         r"text.{0,20}length"]),
    ("UNKNOWN_OUTCOME", False, [r"time[d ]?\s?out", r"timeout", r"\b50[0234]\b",
                                r"bad gateway", r"service unavailable",
                                r"connection (reset|closed|aborted|refused)",
                                r"econnreset", r"socket hang up", r"no response"]),
]


def classify(raw: str) -> dict:
    text = raw.lower()
    for code, retryable, patterns in RULES:
        if any(re.search(pat, text) for pat in patterns):
            return {"error_code": code, "retryable": retryable, "message": raw.strip()}
    return {"error_code": "OTHER", "retryable": False, "message": raw.strip()}


def main() -> int:
    p = argparse.ArgumentParser(description="Classify a LinkedIn connector error.")
    p.add_argument("--error", help="Raw error text or JSON from the connector")
    args = p.parse_args()
    raw = args.error if args.error is not None else sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error_code": "OTHER", "retryable": False,
                          "message": "Empty error from connector"}))
        return 0
    print(json.dumps(classify(raw), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
