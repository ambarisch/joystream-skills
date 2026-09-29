# X weighted-length counting rules

Implemented by `scripts/x_weighted_length.py` (twitter-text v3 configuration). Use these when scripts can't run.

- Limit: 280 weighted characters.
- Weight 1: code points U+0000-U+10FF, U+2000-U+200D, U+2010-U+201F, U+2032-U+2037 (Latin, Greek, Cyrillic, Arabic, Hebrew, Indic scripts, common punctuation).
- Weight 2: everything else (CJK, Japanese, Korean, most symbols).
- Each emoji weighs 2, including multi-code-point sequences (skin tones, ZWJ families, flags, keycaps).
- Each `http://` or `https://` URL weighs 23 regardless of length. Bare domains count as max(real weight, 23).
- Text is NFC-normalised before counting.
