import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "python/evidence.py"
spec = importlib.util.spec_from_file_location("evidence", MODULE)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class Evidence(unittest.TestCase):
    def test_recipient_roundtrip_tampering_wrong_key_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            private, public = base / "recipient.key", base / "recipient.pub"
            evidence.keygen(private, public)
            with self.assertRaises(FileExistsError):
                evidence.keygen(private, public)
            envelope = evidence.encrypt(b"synthetic evidence only", public.read_bytes())
            self.assertNotIn(b"synthetic evidence only", envelope)
            self.assertEqual(evidence.decrypt(envelope, private.read_bytes()), b"synthetic evidence only")
            bad = json.loads(envelope)
            value = bytearray(bad["ciphertext"].encode())
            value[len(value) // 2] = ord('A') if value[len(value) // 2] != ord('A') else ord('B')
            bad["ciphertext"] = value.decode()
            with self.assertRaises(Exception):
                evidence.decrypt(json.dumps(bad).encode(), private.read_bytes())
            other_private, other_public = base / "other.key", base / "other.pub"
            evidence.keygen(other_private, other_public)
            with self.assertRaises(ValueError):
                evidence.decrypt(envelope, other_private.read_bytes())


if __name__ == "__main__":
    unittest.main()
