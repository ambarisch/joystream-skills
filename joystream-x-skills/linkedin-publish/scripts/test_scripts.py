import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args):
    out = subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                         capture_output=True, text=True).stdout
    return json.loads(out)


class Length(unittest.TestCase):
    def count(self, text):
        return run("linkedin_length.py", "--text", text)

    def test_plain(self):
        r = self.count("Hello")
        self.assertEqual(r["weighted_length"], 5)
        self.assertTrue(r["valid"])

    def test_url_counts_full_length(self):
        url = "https://example.com/some/long/path"
        self.assertEqual(self.count(url)["weighted_length"], len(url))

    def test_3000_is_valid(self):
        self.assertTrue(self.count("a" * 3000)["valid"])

    def test_3001_is_too_long(self):
        r = self.count("a" * 3001)
        self.assertFalse(r["valid"])
        self.assertFalse(r["empty"])

    def test_emoji_counts_two(self):
        self.assertEqual(self.count("\U0001F600")["weighted_length"], 2)

    def test_newline_counts_one(self):
        self.assertEqual(self.count("a\nb")["weighted_length"], 3)

    def test_crlf_counts_one(self):
        self.assertEqual(self.count("a\r\nb")["weighted_length"], 3)

    def test_whitespace_is_empty(self):
        r = self.count("   ")
        self.assertFalse(r["valid"])
        self.assertTrue(r["empty"])


class Classify(unittest.TestCase):
    def code(self, err):
        return run("classify_linkedin_error.py", "--error", err)["error_code"]

    def test_codes(self):
        cases = {
            "429 Too Many Requests": "RATE_LIMIT",
            "Daily limit reached for this application": "RATE_LIMIT",
            "HTTP error 402: Payment Required": "RATE_LIMIT",
            "422 Content is a duplicate": "DUPLICATE",
            "401 Unauthorized: invalid access token": "AUTH",
            "REVOKED_ACCESS_TOKEN": "AUTH",
            "403 Not enough permissions to access resource": "FORBIDDEN",
            "Post text too long": "TOO_LONG",
            "ECONNREFUSED: Unable to connect": "AUTH",
            "connection refused": "AUTH",
            "connection reset by peer": "UNKNOWN_OUTCOME",
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
