import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

CODE = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(CODE))
spec = importlib.util.spec_from_file_location("nask_corpus", CODE / "corpus.py")
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


class CorpusIntegrity(unittest.TestCase):
    def setUp(self):
        (corpus.ROOT / "private").mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=corpus.ROOT / "private")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.body = self.path / "fixture.js"
        self.body.write_bytes(b"fetch('/api/synthetic');")

    def row(self, origin="https://dns.pl"):
        return {"file": str(self.body), "origin": origin, "source_url": "archive:synthetic",
                "source_attribution": "synthetic", "sha256": hashlib.sha256(self.body.read_bytes()).hexdigest()}

    def load(self, rows):
        manifest = self.path / "inventory.json"
        manifest.write_text(json.dumps(rows), encoding="utf-8")
        return corpus.load_corpus(manifest)

    def test_copies_preserve_provenance_but_different_origins_stay_separate(self):
        docs, counts = self.load([self.row(), self.row(), self.row("https://oad.nask.pl")])
        self.assertEqual(len(docs), 2)
        self.assertEqual(len(docs[0]["provenance"]), 2)
        self.assertEqual(counts["duplicate_observations"], 1)
        self.assertEqual({d["program"] for d in docs}, {"nask"})

    def test_hash_tampering_is_rejected(self):
        row = self.row()
        self.body.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash"):
            self.load([row])

    def test_other_program_alias_and_noncanonical_origins_are_rejected(self):
        for origin in ["https://cert.pl", "https://www.nask.pl", "https://dns.pl/path", "https://dns.pl:443", "http://dns.pl"]:
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self.load([self.row(origin)])

    def test_files_outside_private_are_rejected(self):
        row = self.row()
        row["file"] = str(corpus.ROOT / "README.md")
        with self.assertRaisesRegex(ValueError, "outside private"):
            self.load([row])


if __name__ == "__main__":
    unittest.main()
