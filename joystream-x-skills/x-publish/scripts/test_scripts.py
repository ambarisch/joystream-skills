import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args):
    import json
    out = subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                         capture_output=True, text=True).stdout
    return json.loads(out)


class WeightedLength(unittest.TestCase):
    def count(self, text):
        return run("x_weighted_length.py", "--text", text)

    def test_plain(self):
        r = self.count("Hello")
        self.assertEqual(r["weighted_length"], 5)
        self.assertTrue(r["valid"])

    def test_url_counts_23(self):
        r = self.count("Hello \U0001F44B https://example.com/some/long/path")
        self.assertEqual(r["weighted_length"], 32)

    def test_281_plain_is_too_long(self):
        r = self.count("a" * 281)
        self.assertFalse(r["valid"])
        self.assertFalse(r["empty"])

    def test_280_plain_is_valid(self):
        self.assertTrue(self.count("a" * 280)["valid"])

    def test_whitespace_is_empty(self):
        r = self.count("   ")
        self.assertFalse(r["valid"])
        self.assertTrue(r["empty"])

    def test_emoji_and_newline(self):
        self.assertEqual(self.count("hi \U0001F600\nyo")["weighted_length"], 8)


class Classify(unittest.TestCase):
    def code(self, err):
        return run("classify_x_error.py", "--error", err)["error_code"]

    def test_codes(self):
        cases = {
            "429 Too Many Requests": "RATE_LIMIT",
            "403 Forbidden: duplicate content": "DUPLICATE",
            "401 Unauthorized": "AUTH",
            "403 account suspended": "FORBIDDEN",
            "Tweet text too long": "TOO_LONG",
            "502 Bad Gateway": "UNKNOWN_OUTCOME",
            "request timed out": "UNKNOWN_OUTCOME",
            "something odd": "OTHER",
        }
        for err, want in cases.items():
            with self.subTest(err=err):
                self.assertEqual(self.code(err), want)

    def test_never_emits_no_tool(self):
        self.assertNotEqual(self.code("no tool available"), "NO_TOOL")


if __name__ == "__main__":
    unittest.main()
