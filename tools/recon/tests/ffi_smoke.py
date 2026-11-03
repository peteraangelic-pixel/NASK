"""Exercise the real native library on public synthetic fixtures only."""
import argparse
import importlib.util
from pathlib import Path

module = Path(__file__).resolve().parents[1] / "python/nasklab.py"
spec = importlib.util.spec_from_file_location("nasklab", module)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
parser = argparse.ArgumentParser()
parser.add_argument("--library", type=Path, required=True)
args = parser.parse_args()
documents = [
    {"program": "fixture-a", "source_url": "https://a.invalid/", "body": '<form><input type="file"></form>'},
    {"program": "fixture-b", "source_url": "https://b.invalid/a.js", "body": "fetch('/api/example'); // żółw 🐢"},
    {"program": "fixture-c", "source_url": "https://c.invalid/modernizr-custom.js", "body": "new FormData(); input.type='file'"},
]
result = lab.analyze(documents, args.library, 2)
assert result["confirmed_vulnerabilities"] == 0
assert result["documents"][0]["upload_surface"]
assert result["documents"][1]["route_literals"] == ["/api/example"]
assert result["documents"][1]["source_url"] == "https://b.invalid/a.js"
assert not result["documents"][2]["upload_surface"]
assert result["documents"][2]["multipart_capability_mention"]
assert result["documents"][2]["file_control_mention"]
assert result["documents"][2]["triage_score"] == 0
try:
    lab.analyze(documents, args.library, 0)
except ValueError:
    pass
else:
    raise AssertionError("FFI accepted invalid thread count")
print("Rust/Python FFI: synthetic roundtrip and error path passed")
