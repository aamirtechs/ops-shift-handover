import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops_shift_handover import render_md, render_txt, sort_incidents, validate  # noqa: E402

GOOD = {
    "date": "2026-10-28", "shift": "Night", "team": "Support",
    "outgoing": "Ayesha", "incoming": "Bilal",
    "summary": ["Queue cleared to zero."],
    "open_incidents": [
        {"id": "INC-1002", "severity": "low", "title": "Slow report",
         "status": "open", "next_step": "Recheck after deploy."},
        {"id": "INC-1001", "severity": "critical", "title": "Checkout down",
         "status": "investigating", "next_step": "Page the on-call."},
    ],
    "pending_tasks": ["Reply to ticket 4521."],
    "watch_items": ["Traffic spike at 10:00."],
}


class TestValidate(unittest.TestCase):
    def test_good_input_valid(self):
        self.assertEqual(validate(GOOD), [])

    def test_missing_fields_reported(self):
        problems = validate({"date": "2026-10-28"})
        for field in ("shift", "team", "outgoing", "incoming"):
            self.assertIn(f"missing required field: {field}", problems)

    def test_non_list_summary_reported(self):
        bad = dict(GOOD, summary="not a list")
        self.assertIn("summary must be a list of strings", validate(bad))

    def test_incident_missing_title_reported(self):
        bad = dict(GOOD, open_incidents=[{"id": "INC-1", "status": "open"}])
        self.assertIn("open incident missing required field: title",
                      validate(bad))


class TestRender(unittest.TestCase):
    def test_critical_incident_first(self):
        text = render_md(GOOD)
        self.assertLess(text.index("INC-1001"), text.index("INC-1002"))

    def test_sections_present(self):
        text = render_md(GOOD)
        self.assertIn("Shift handover: Support, Night shift, 2026-10-28", text)
        self.assertIn("Outgoing: Ayesha", text)
        self.assertIn("Pending tasks", text)
        self.assertIn("Reply to ticket 4521.", text)

    def test_empty_handover_says_all_clear(self):
        minimal = {"date": "2026-10-28", "shift": "Day", "team": "Support",
                   "outgoing": "Ayesha", "incoming": "Bilal"}
        self.assertIn("All clear", render_md(minimal))

    def test_txt_has_no_markdown(self):
        text = render_txt(GOOD)
        self.assertNotIn("**", text)
        self.assertNotIn("## ", text)
        self.assertIn("INC-1001", text)

    def test_sort_unknown_severity_last(self):
        incidents = [
            {"id": "INC-9", "severity": "weird"},
            {"id": "INC-1", "severity": "high"},
        ]
        self.assertEqual(sort_incidents(incidents)[0]["id"], "INC-1")


class TestCli(unittest.TestCase):
    def run_cli(self, data, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handover.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "ops_shift_handover.py"),
                 str(path), *args],
                capture_output=True, text=True)
            return result

    def test_human_output(self):
        result = self.run_cli(GOOD)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Shift handover", result.stdout)
        self.assertIn("INC-1001", result.stdout)

    def test_check_passes_and_fails(self):
        self.assertEqual(self.run_cli(GOOD, "--check").returncode, 0)
        bad = {"date": "2026-10-28"}
        self.assertEqual(self.run_cli(bad, "--check").returncode, 1)

    def test_template_is_valid_input(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "ops_shift_handover.py"), "--template"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(validate(json.loads(result.stdout)), [])

    def test_txt_format(self):
        result = self.run_cli(GOOD, "--format", "txt")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("**", result.stdout)


if __name__ == "__main__":
    unittest.main()
