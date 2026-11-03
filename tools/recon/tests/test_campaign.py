import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(SOURCE))
import campaign
import evidence


class Campaign(unittest.TestCase):
    def test_missing_or_duplicate_root_records_fail_and_preserve_encrypted_receipt(self):
        for root_rows in ([], ["https://a.invalid/", "https://a.invalid/"]):
            with self.subTest(rows=len(root_rows)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "tools/recon").mkdir(parents=True)
                (root / "tools/recon/Cargo.lock").write_text("fixture")
                (root / "tools/recon/Cargo.toml").write_text("fixture")
                manifest = root / "manifest.json"
                manifest.write_text("{}")
                library = root / "fixture.dll"
                library.write_bytes(b"fixture only")
                private, public = root / "recipient.key", root / "recipient.pub"
                evidence.keygen(private, public)
                request = root / "request.json"
                request.write_text(json.dumps({"schema_version": 1, "id": "test", "operation": "public-surface-validation",
                                              "programs": ["fixture"], "rps": 1, "requests": 2, "workers": 1}))
                def fake_subprocess(args, check):
                    if "collect" in args:
                        run_dir = Path(args[args.index("--run-dir") + 1])
                        run_dir.mkdir(parents=True)
                        rows = [{"source_url": u, "sequence": i + 1, "status": 200, "error": None}
                                for i, u in enumerate(root_rows)]
                        (run_dir / "requests.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
                    return SimpleNamespace(returncode=0)
                with patch.object(campaign, "ROOT", root), patch.object(campaign, "MANIFEST", manifest), \
                     patch.object(campaign, "Scope", lambda *_: SimpleNamespace(seeds=lambda: ["https://a.invalid/"])), \
                     patch.object(campaign.subprocess, "run", fake_subprocess):
                    with self.assertRaises(SystemExit):
                        campaign.run(request, library, public)
                summary = json.loads((root / "private/public-summary.json").read_text())
                self.assertFalse(summary["complete_root_records"])
                self.assertEqual(summary["requests_issued"], len(root_rows))
                data = evidence.decrypt((root / "private/campaign.enc").read_bytes(), private.read_bytes())
                self.assertTrue(data.startswith(b"\x1f\x8b"))

    def test_duplicate_spec_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"requests":1,"requests":48}', object_pairs_hook=campaign.unique_object)


if __name__ == "__main__":
    unittest.main()
