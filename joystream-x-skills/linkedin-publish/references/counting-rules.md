# LinkedIn length counting rules

Implemented by `scripts/linkedin_length.py`. Use these when scripts can't run.

- Limit: 3000 characters.
- Text is NFC-normalised before counting.
- Length is counted in UTF-16 code units. Most characters count 1; emoji and other characters outside the Basic Multilingual Plane count 2.
- Line breaks count 1 each (`\r\n` counts 1).
- URLs count at their full length. LinkedIn does not shorten them for counting.

The counting is deliberately conservative: it can reject a borderline post LinkedIn might accept, but should not accept one LinkedIn rejects. It has not been verified against LinkedIn's own counter, so if a post of about 3000 characters is rejected or accepted unexpectedly, adjust these rules and `scripts/linkedin_length.py` together.
