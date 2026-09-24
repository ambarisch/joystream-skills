#!/usr/bin/env python3
"""
Map a raw error from the X connector to a stable error code, so callers can
branch on a code instead of interpreting free-form error text.

Usage:
  python3 classify_x_error.py --error "429 Too Many Requests"
  echo "<raw error text or JSON>" | python3 classify_x_error.py

Prints JSON: {"error_code": "RATE_LIMIT", "retryable": true, "message": "..."}

Codes (checked in this order, first match wins):
  DUPLICATE        X rejected identical recent content (often sent as a 403)
  RATE_LIMIT       429 / too many requests / usage cap reached
  AUTH             401, missing/expired/revoked token, connector not connected
  FORBIDDEN        403 for any other reason (suspended, locked, not permitted)
  TOO_LONG         X itself rejected the length
  UNKNOWN_OUTCOME  timeout, connection dropped, 5xx: the post MAY have gone out
  OTHER            anything else
"""
import argparse
import json
import re
import sys

RULES = [
    ("DUPLICATE", False, [r"duplicate"]),
    ("RATE_LIMIT", True, [r"\b429\b", r"too many requests", r"rate.?limit",
                          r"usage.?cap", r"quota"]),
    ("AUTH", False, [r"\b401\b", r"unauthori[sz]ed", r"not authenticated",
                     r"authenticat", r"invalid.{0,20}token", r"expired.{0,20}token",
                     r"token.{0,20}(expired|revoked|invalid)", r"credential",
                     r"not connected", r"reconnect", r"oauth"]),
    ("FORBIDDEN", False, [r"\b403\b", r"forbidden", r"not permitted",
                          r"not allowed", r"suspended", r"locked"]),
    ("TOO_LONG", False, [r"too long", r"exceeds?.{0,30}(length|characters|280)",
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
    p = argparse.ArgumentParser(description="Classify an X connector error.")
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
