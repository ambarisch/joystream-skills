#!/usr/bin/env python3
"""
Count a post's length the way X (Twitter) does, using only the Python
standard library (no network, no third-party packages).

Rules implemented (twitter-text v3 configuration):
  * Limit: 280 weighted characters.
  * Code points in these ranges weigh 1: U+0000-U+10FF, U+2000-U+200D,
    U+2010-U+201F, U+2032-U+2037 (Latin, Greek, Cyrillic, Arabic, Hebrew,
    Indic scripts such as Devanagari and Kannada, common punctuation).
    Everything else (CJK, Japanese, Korean, most symbols) weighs 2.
  * Each emoji weighs 2, including multi-code-point sequences
    (skin tones, ZWJ families, flags, keycaps).
  * Each URL weighs 23, whatever its real length.
  * Text is NFC-normalised before counting (for counting only).

URLs with http:// or https:// are always counted as 23. Bare domains
(e.g. "example.com/page") are only sometimes linked by X, so they are
counted conservatively as max(real weight, 23). This can reject a
borderline post X would accept, but never accepts one X would reject.

Usage:
  python3 x_weighted_length.py --text "Hello world"
  echo "Hello world" | python3 x_weighted_length.py
  python3 x_weighted_length.py --file post.txt

Prints JSON:
  {"weighted_length": 11, "limit": 280, "remaining": 269,
   "valid": true, "empty": false, "urls": [], "possible_urls": []}
Exit code 0 when valid, 1 when empty or too long, 2 on usage error.
"""
import argparse
import json
import re
import sys
import unicodedata

LIMIT = 280
URL_WEIGHT = 23

LIGHT_RANGES = (
    (0x0000, 0x10FF),
    (0x2000, 0x200D),
    (0x2010, 0x201F),
    (0x2032, 0x2037),
)

SCHEME_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
BARE_DOMAIN_RE = re.compile(
    r"(?<![@\w./-])(?:www\.)?[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*"
    r"\.(?:com|org|net|io|ai|co|in|dev|app|me|ly|gg|tv|edu|gov|info|xyz|"
    r"tech|so|us|uk|biz|site|online|store|blog|news|page)"
    r"(?:/[^\s]*)?(?![\w-])",
    re.IGNORECASE,
)
TRAILING_PUNCT = ".,!?:;)]}'\"…"


def _is_emoji_base(cp: int) -> bool:
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or 0x2300 <= cp <= 0x23FF
        or 0x2B00 <= cp <= 0x2BFF
        or 0x2190 <= cp <= 0x21FF
        or cp in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299)
    )


def _is_emoji_modifier(cp: int) -> bool:
    return (
        cp == 0xFE0F
        or cp == 0x20E3
        or 0x1F3FB <= cp <= 0x1F3FF
        or 0xE0020 <= cp <= 0xE007F
    )


def _char_weight(cp: int) -> int:
    for lo, hi in LIGHT_RANGES:
        if lo <= cp <= hi:
            return 1
    return 2


def _weigh_plain(text: str) -> int:
    """Weigh text that contains no URLs."""
    cps = [ord(c) for c in text]
    i, total, n = 0, 0, len(cps)
    while i < n:
        cp = cps[i]
        # Keycap: [0-9#*] FE0F? 20E3
        if chr(cp) in "0123456789#*":
            j = i + 1
            if j < n and cps[j] == 0xFE0F:
                j += 1
            if j < n and cps[j] == 0x20E3:
                total += 2
                i = j + 1
                continue
        # Flag: pair of regional indicators
        if 0x1F1E6 <= cp <= 0x1F1FF:
            i += 2 if i + 1 < n and 0x1F1E6 <= cps[i + 1] <= 0x1F1FF else 1
            total += 2
            continue
        if _is_emoji_base(cp):
            i += 1
            while i < n:
                if _is_emoji_modifier(cps[i]):
                    i += 1
                elif cps[i] == 0x200D and i + 1 < n:
                    i += 2  # ZWJ + next component
                else:
                    break
            total += 2
            continue
        total += _char_weight(cp)
        i += 1
    return total


def _strip_trailing(url: str) -> str:
    while url and url[-1] in TRAILING_PUNCT:
        url = url[:-1]
    return url


def count(text: str) -> dict:
    norm = unicodedata.normalize("NFC", text)
    urls, possible = [], []
    spans = []  # (start, end, weight)

    for m in SCHEME_URL_RE.finditer(norm):
        url = _strip_trailing(m.group(0))
        if not url:
            continue
        spans.append((m.start(), m.start() + len(url), URL_WEIGHT))
        urls.append(url)

    def overlaps(s, e):
        return any(s < se and e > ss for ss, se, _ in spans)

    for m in BARE_DOMAIN_RE.finditer(norm):
        url = _strip_trailing(m.group(0))
        s, e = m.start(), m.start() + len(url)
        if not url or overlaps(s, e):
            continue
        spans.append((s, e, max(_weigh_plain(url), URL_WEIGHT)))
        possible.append(url)

    spans.sort()
    total, pos = 0, 0
    for s, e, w in spans:
        total += _weigh_plain(norm[pos:s]) + w
        pos = e
    total += _weigh_plain(norm[pos:])

    empty = norm.strip() == ""
    return {
        "weighted_length": total,
        "limit": LIMIT,
        "remaining": LIMIT - total,
        "valid": (not empty) and total <= LIMIT,
        "empty": empty,
        "urls": urls,
        "possible_urls": possible,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Count text the way X does.")
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
