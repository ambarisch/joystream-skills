#!/usr/bin/env python3
"""
Count a post's length conservatively for LinkedIn, using only the Python
standard library (no network, no third-party packages).

Rules implemented:
  * Limit: 3000 characters.
  * Text is NFC-normalised before counting.
  * Length is counted in UTF-16 code units (emoji and other characters
    outside the Basic Multilingual Plane count 2).
  * Line breaks count 1 (\\r\\n counts 1).
  * URLs count at their full length.

This can reject a borderline post LinkedIn would accept, but should not
accept one LinkedIn would reject. It has not been checked against LinkedIn's
own counter.

Usage:
  python3 linkedin_length.py --text "Hello world"
  echo "Hello world" | python3 linkedin_length.py
  python3 linkedin_length.py --file post.txt

Prints JSON:
  {"weighted_length": 11, "limit": 3000, "remaining": 2989,
   "valid": true, "empty": false}
Exit code 0 when valid, 1 when empty or too long, 2 on usage error.
"""
import argparse
import json
import sys
import unicodedata

LIMIT = 3000


def count(text: str) -> dict:
    norm = unicodedata.normalize("NFC", text).replace("\r\n", "\n")
    total = len(norm.encode("utf-16-le")) // 2
    empty = norm.strip() == ""
    return {
        "weighted_length": total,
        "limit": LIMIT,
        "remaining": LIMIT - total,
        "valid": (not empty) and total <= LIMIT,
        "empty": empty,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Count text for LinkedIn.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--text", help="Post text")
    g.add_argument("--file", help="Path to a UTF-8 file containing the post text")
    args = p.parse_args()

    if args.text is not None:
        text = args.text
    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        # A single trailing newline from echo/heredoc is not part of the post
        if text.endswith("\n"):
            text = text[:-1]
    else:
        p.print_usage(sys.stderr)
        return 2

    result = count(text)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
