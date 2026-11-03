"""Versioned collection/analysis operation with a coverage receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from nasklab import MANIFEST, ROOT, Scope
from evidence import encrypt


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def run(request_file: Path, library: Path, recipient: Path):
    spec = json.loads(request_file.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    fields = {"schema_version", "id", "operation", "programs", "rps", "requests", "workers"}
    if (set(spec) != fields or spec["schema_version"] != 1
            or not re.fullmatch(r"[a-z0-9-]{1,70}", spec["id"])
            or spec["operation"] != "public-surface-validation"
            or type(spec["rps"]) not in (int, float) or not 0 < spec["rps"] <= 1
            or type(spec["requests"]) is not int or not 1 <= spec["requests"] <= 48
            or type(spec["workers"]) is not int or not 1 <= spec["workers"] <= 2
            or type(spec["programs"]) is not list or not spec["programs"]
            or len(set(spec["programs"])) != len(spec["programs"])):
        raise ValueError("unreviewed campaign specification")
    scope = Scope(json.loads(MANIFEST.read_text(encoding="utf-8")), spec["programs"])
    planned = scope.seeds()[:spec["requests"]]
    code_files = sorted((ROOT / "tools/recon/python").glob("*.py")) + sorted((ROOT / "tools/recon/src").glob("*.rs"))
    code_files += [ROOT / "tools/recon/Cargo.lock", ROOT / "tools/recon/Cargo.toml"]
    code_hash = hashlib.sha256()
    for file in code_files:
        code_hash.update(str(file.relative_to(ROOT)).replace("\\", "/").encode() + b"\0")
        code_hash.update(hashlib.sha256(file.read_bytes()).digest())
    identity = {"spec": spec, "code_sha256": code_hash.hexdigest(),
                "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest()}
    batch_id = hashlib.sha256(canonical(identity)).hexdigest()
    attempt = os.environ.get("GITHUB_RUN_ID", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
    run_dir = ROOT / "private/runs" / f"{spec['id']}-{attempt}"
    args = [sys.executable, str(Path(__file__).with_name("nasklab.py")), "collect"]
    for p in spec["programs"]:
        args += ["--program", p]
    args += ["--run-dir", str(run_dir), "--rps", str(spec["rps"]), "--requests", str(spec["requests"]),
             "--workers", str(spec["workers"]), "--execute"]
    result = subprocess.run(args, check=False)
    receipt = {**identity, "batch_id": batch_id, "attempt": attempt, "collection_exit": result.returncode,
               "commit": os.environ.get("GITHUB_SHA"), "expected_roots": planned,
               "started_targets": 0, "confirmed_vulnerabilities": 0}
    run_dir.mkdir(parents=True, exist_ok=True)
    log_file = run_dir / "requests.jsonl"
    rows = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()] if log_file.exists() else []
    roots = [row["source_url"] for row in rows if row["source_url"] in planned]
    receipt["complete_root_records"] = len(roots) == len(set(roots)) == len(planned) and set(roots) == set(planned)
    receipt["started_targets"] = sum(row["sequence"] is not None for row in rows)
    receipt["http_responses"] = sum(row["status"] > 0 for row in rows)
    receipt["transport_or_control_errors"] = sum(bool(row["error"]) for row in rows)
    if result.returncode == 0:
        analysis = subprocess.run([sys.executable, str(Path(__file__).with_name("nasklab.py")), "analyze",
                                   "--run-dir", str(run_dir), "--library", str(library), "--threads", "4"], check=False)
        receipt["analysis_exit"] = analysis.returncode
    else:
        receipt["analysis_exit"] = None
    (run_dir / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    archive = ROOT / "private/campaign.tar.gz"
    with tarfile.open(archive, "w:gz") as output:
        output.add(run_dir, arcname="run")
    envelope = encrypt(archive.read_bytes(), recipient.read_bytes())
    (ROOT / "private/campaign.enc").write_bytes(envelope)
    summary = {key: receipt[key] for key in ["batch_id", "attempt", "collection_exit", "analysis_exit",
              "complete_root_records", "started_targets", "http_responses", "transport_or_control_errors", "confirmed_vulnerabilities"]}
    (ROOT / "private/public-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    if result.returncode != 0 or receipt["analysis_exit"] != 0 or not receipt["complete_root_records"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--recipient", type=Path, required=True)
    options = parser.parse_args()
    run(options.request, options.library, options.recipient)
