"""
Tests for the MVP generator. No network, no API key.

The Anthropic client is stubbed, so what is under test is our half: finding the
target spreadsheet, shaping the request, and pulling the code back out of the
reply.

Run:  .venv/bin/python -m unittest mvp.test_generate -v
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from mvp import generate as g


def fake_reply(text, stop_reason="end_turn"):
    """A stand-in for the streamed message the SDK returns."""
    message = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
    )
    stream = mock.MagicMock()
    stream.__enter__.return_value.get_final_message.return_value = message
    client = mock.MagicMock()
    client.messages.stream.return_value = stream
    return client


REPLY = """This adds a Days Since Start column.

```javascript
function addDaysSinceStart() {
  var sheet = SpreadsheetApp.openById('abc').getActiveSheet();
}
```"""


class TestFindSpreadsheetId(unittest.TestCase):
    def test_full_url(self):
        self.assertEqual(
            g.find_spreadsheet_id(
                "see https://docs.google.com/spreadsheets/d/"
                "1ExampleFakeSheetIdForTestsOnly_0123456789A/edit#gid=0 please"),
            "1ExampleFakeSheetIdForTestsOnly_0123456789A")

    def test_bare_id(self):
        self.assertEqual(
            g.find_spreadsheet_id("use 1ExampleFakeSheetIdForTestsOnly_0123456789A"),
            "1ExampleFakeSheetIdForTestsOnly_0123456789A")

    def test_no_id_returns_none(self):
        self.assertIsNone(g.find_spreadsheet_id("sort the sheet by last name"))

    def test_ordinary_prose_is_not_mistaken_for_an_id(self):
        """The length floor is what stops long words matching."""
        self.assertIsNone(g.find_spreadsheet_id(
            "please reconcile the internationalisation spreadsheet thoroughly"))


class TestBuildUserMessage(unittest.TestCase):
    def test_id_present_uses_openById(self):
        msg = g.build_user_message("do a thing", "SHEET123")
        self.assertIn("openById('SHEET123')", msg)

    def test_id_absent_uses_active_spreadsheet(self):
        msg = g.build_user_message("do a thing", None)
        self.assertIn("getActiveSpreadsheet()", msg)
        self.assertNotIn("openById", msg)


class TestGenerate(unittest.TestCase):
    def test_happy_path_splits_explanation_from_code(self):
        with mock.patch.object(g.anthropic, "Anthropic", return_value=fake_reply(REPLY)):
            out = g.generate("add a column, sheet "
                             "1ExampleFakeSheetIdForTestsOnly_0123456789A",
                             api_key="test")
        self.assertEqual(out["explanation"], "This adds a Days Since Start column.")
        self.assertTrue(out["code"].startswith("function addDaysSinceStart()"))
        self.assertNotIn("```", out["code"])
        self.assertEqual(out["spreadsheet_id"],
                         "1ExampleFakeSheetIdForTestsOnly_0123456789A")

    def test_reply_without_a_code_block_is_an_error(self):
        with mock.patch.object(g.anthropic, "Anthropic",
                               return_value=fake_reply("I need more detail.")):
            with self.assertRaises(g.GenerationError):
                g.generate("something vague", api_key="test")

    def test_refusal_is_surfaced_not_swallowed(self):
        with mock.patch.object(g.anthropic, "Anthropic",
                               return_value=fake_reply(REPLY, stop_reason="refusal")):
            with self.assertRaises(g.GenerationError):
                g.generate("anything", api_key="test")

    def test_empty_query_rejected_before_any_api_call(self):
        with mock.patch.object(g.anthropic, "Anthropic") as client:
            with self.assertRaises(g.GenerationError):
                g.generate("   ", api_key="test")
            client.assert_not_called()

    def test_missing_key_is_a_readable_error(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(g.GenerationError) as ctx:
                g.generate("do a thing")
        self.assertIn("ANTHROPIC_API_KEY", str(ctx.exception))

    def test_generated_code_parses_as_javascript(self):
        """A reply that is not valid JS should not reach the user as if it were."""
        with mock.patch.object(g.anthropic, "Anthropic", return_value=fake_reply(REPLY)):
            out = g.generate("add a column", api_key="test")
        import shutil, subprocess, tempfile, pathlib
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        p = pathlib.Path(tempfile.mkdtemp()) / "s.js"
        p.write_text(out["code"])
        self.assertEqual(subprocess.run([node, "--check", str(p)],
                                        capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
