from datetime import date
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import night
import evidence

MANIFEST = json.loads(night.MANIFEST.read_text(encoding="utf-8"))


class Response(io.BytesIO):
    def __init__(self, url, code, data):
        super().__init__(data)
        self.code, self.url = code, url
        self.headers = {"Content-Type": "text/plain"}

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, code=200, data=b"fixture"):
        self.code, self.data, self.calls = code, data, []

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        return Response(request.full_url, self.code, self.data)


class NightControls(unittest.TestCase):
    def scope(self):
        return night.Scope(MANIFEST, ["gov-pl"], today=date(2026, 11, 3))

    def test_arbitrary_operation_and_duplicate_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "spec.json"
            path.write_text(json.dumps({**night.EXPECTED, "rps": 5}))
            with self.assertRaises(ValueError): night.specification(path)
            path.write_text('{"rps":1,"rps":5}')
            with self.assertRaises(ValueError): night.specification(path)

    def test_changed_terms_stop_before_target_requests(self):
        opener, receipt = Opener(data=b"%PDF synthetic changed terms"), {}
        with self.assertRaises(ValueError):
            night.refreshed_scope(MANIFEST, night.Governor(5, 100), opener, receipt)
        self.assertEqual(len(opener.calls), 1)
        self.assertTrue(opener.calls[0].startswith("https://hack.cert.pl/api/"))
        self.assertFalse(receipt["terms_checks"][0]["matched"])

    def test_capture_bounds_and_scope_before_transport(self):
        opener = Opener(data=b"x" * 70000)
        with tempfile.TemporaryDirectory() as folder:
            result = night.capture("https://www.gov.pl/.env", "environment", self.scope(),
                                   night.Governor(5, 1), Path(folder), opener)
            self.assertTrue(result["truncated"])
            self.assertEqual((Path(folder) / result["body_file"]).stat().st_size, 65536)
            with self.assertRaises(ValueError):
                night.capture("https://gov.pl/.env", "environment", self.scope(),
                              night.Governor(5, 1), Path(folder), opener)
            self.assertEqual(len(opener.calls), 1)

    def test_host_block_rate_limit_and_deadline_prevent_further_requests(self):
        for status, deadline, expected_calls in [(403, float("inf"), 1), (429, float("inf"), 1), (200, -1, 0)]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as folder:
                opener = Opener(status)
                governor = night.Governor(5, 100)
                rows = night.collect(self.scope(), governor, Path(folder), opener, "fixture", deadline)
                self.assertEqual(len(rows), 4)
                self.assertEqual(len(opener.calls), expected_calls)
                self.assertTrue(all(r["sequence"] is None for r in rows[expected_calls:]))
                if status == 429: self.assertTrue(governor.stopped.is_set())

    def test_complete_plan_only_uses_four_fixed_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            opener = Opener(404)
            rows = night.collect(self.scope(), night.Governor(5, 100), Path(folder), opener, "fixture", float("inf"))
            self.assertEqual([r["request_path"] for r in rows], [
                "/nasklab-missing-fixture-a", "/nasklab-missing-fixture-b", "/.git/HEAD", "/.env"])
            self.assertEqual(len(opener.calls), 4)

    def test_failed_preflight_preserves_encrypted_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request, library = root / "request.json", root / "library.dll"
            request.write_text(json.dumps(night.EXPECTED))
            library.write_bytes(b"fixture only")
            private, public = root / "recipient.key", root / "recipient.pub"
            evidence.keygen(private, public)
            with patch.object(night, "ROOT", root), \
                 patch.object(night, "refreshed_scope", side_effect=ValueError("fixture")), \
                 patch.dict(night.os.environ, {"GITHUB_ACTIONS": "true", "NASKLAB_OPERATION": night.EXPECTED["operation"]}):
                self.assertEqual(night.run(request, library, public), 2)
            summary = json.loads((root / "private/night/public-summary.json").read_text())
            self.assertEqual(summary["target_requests"], 0)
            self.assertEqual(summary["status"], "failed")
            archive = evidence.decrypt((root / "private/night/campaign.enc").read_bytes(), private.read_bytes())
            self.assertTrue(archive.startswith(b"\x1f\x8b"))


if __name__ == "__main__":
    unittest.main()
