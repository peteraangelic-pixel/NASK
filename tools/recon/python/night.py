"""One bounded, explicitly reviewed exposure-check operation; no exploit chaining."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from zoneinfo import ZoneInfo

from campaign import canonical, unique_object
from evidence import encrypt
from nasklab import Governor, MANIFEST, NoRedirect, ROOT, Scope, analyze, load_documents, network_lock

EXPECTED = {"schema_version": 1, "id": "night-exposure-20261103-v1",
            "operation": "bounded-file-exposure-v1",
            "programs": ["nask", "cert-polska", "gov-pl", "wladyslawowo"],
            "rps": 1, "max_requests_including_terms": 100,
            "max_body_bytes": 65536, "deadline_seconds": 600}
CHECKS = [("control-a", "/nasklab-missing-{nonce}-a"),
          ("control-b", "/nasklab-missing-{nonce}-b"),
          ("git-head", "/.git/HEAD"), ("environment", "/.env")]


def specification(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if canonical(spec) != canonical(EXPECTED):
        raise ValueError("operation differs from the reviewed fixed specification")
    return spec


def refreshed_scope(manifest: dict, governor: Governor, opener, receipt: dict) -> Scope:
    """A changed document stops before any target request, including after midnight."""
    reviewed = copy.deepcopy(manifest)
    receipt["terms_checks"] = []
    for program_id in EXPECTED["programs"]:
        program = next(p for p in reviewed["programs"] if p["id"] == program_id)
        url = program["terms_url"]
        if not url.startswith("https://hack.cert.pl/api/v1/public/") or urlsplit(url).hostname != "hack.cert.pl":
            raise ValueError("unreviewed terms endpoint")
        governor.acquire()
        request = Request(url, headers={"User-Agent": "NASKLab/0.2 terms-verification"})
        with opener.open(request, timeout=15) as response:
            if response.geturl() != url or response.code != 200:
                raise ValueError("terms unavailable or redirected")
            body = response.read(4_000_001)
        digest = hashlib.sha256(body).hexdigest()
        matched = len(body) <= 4_000_000 and body.startswith(b"%PDF") and digest == program["terms_sha256"]
        receipt["terms_checks"].append({"program": program_id, "sha256": digest, "matched": matched})
        if not matched:
            raise ValueError("terms changed; human review required before target requests")
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    reviewed["verified_on"] = today.isoformat()
    receipt["runtime_terms_verified_on"] = today.isoformat()
    return Scope(reviewed, EXPECTED["programs"], today=today)


def capture(url: str, check: str, scope: Scope, governor: Governor, directory: Path, opener) -> dict:
    scope.validate(url)
    parsed = urlsplit(url)
    row = {"source_url": url, "origin": f"https://{parsed.hostname}", "request_path": parsed.path,
           "check": check, **scope.hosts[parsed.hostname], "sequence": None,
           "status": 0, "error": None, "truncated": False, "body_file": None}
    response = None
    try:
        row["sequence"] = governor.acquire()
        row["started_at"] = datetime.now(timezone.utc).isoformat()
        request = Request(url, headers={"User-Agent": "NASKLab/0.2 authorized-bounty-readonly-check",
                                       "Accept-Encoding": "identity"})
        try:
            response = opener.open(request, timeout=8)
        except HTTPError as error:
            response = error
        row["status"] = response.code
        if response.geturl() != url:
            raise ValueError("unexpected redirect")
        row["content_type"] = response.headers.get("Content-Type", "")
        if row["status"] in (301, 302, 303, 307, 308):
            row["error"] = "redirect_not_followed"
        elif row["status"] == 429:
            row["error"] = "rate_limited_no_retry"
            governor.stopped.set()
        elif row["status"] in (200, 404):
            raw = response.read(EXPECTED["max_body_bytes"] + 1)
            row["truncated"] = len(raw) > EXPECTED["max_body_bytes"]
            body = raw[:EXPECTED["max_body_bytes"]]
            if not governor.accept_body(len(body)):
                raise ValueError("aggregate body budget exhausted")
            row["sha256"] = hashlib.sha256(body).hexdigest()
            name = f"{row['sequence']:03d}-{row['sha256'][:16]}.body"
            (directory / name).write_bytes(body)
            row["body_file"], row["bytes"] = name, len(body)
    except (OSError, URLError, ValueError) as error:
        row["error"] = type(error).__name__
    finally:
        if response is not None:
            response.close()
    return row


def collect(scope: Scope, governor: Governor, directory: Path, opener, nonce: str, deadline: float) -> list[dict]:
    rows, blocked = [], set()
    # Complete each stage across all programs first; one coordinator, no independent runners.
    with (directory / "requests.jsonl").open("x", encoding="utf-8") as output:
        for check, template in CHECKS:
            for root in scope.seeds():
                url = root.rstrip("/") + template.format(nonce=nonce)
                if time.monotonic() >= deadline:
                    governor.stopped.set()
                if root in blocked or governor.stopped.is_set():
                    row = {"source_url": url, "check": check, "sequence": None, "status": 0,
                           "error": "skipped_global_stop" if governor.stopped.is_set() else "skipped_host", "body_file": None}
                else:
                    row = capture(url, check, scope, governor, directory, opener)
                    if row["error"] or row["status"] in (401, 403) or row["status"] >= 500:
                        blocked.add(root)
                rows.append(row)
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
                output.flush()
    return rows


def run(request_file: Path, library: Path, recipient: Path) -> int:
    spec = specification(request_file)
    attempt = os.environ.get("GITHUB_RUN_ID", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
    if not re.fullmatch(r"[A-Za-z0-9-]{1,40}", attempt):
        raise ValueError("invalid attempt id")
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("NASKLAB_OPERATION") != spec["operation"]:
        raise ValueError("this fixed operation is enabled only by the reviewed Actions workflow")
    folder = ROOT / "private/night"
    folder.mkdir(parents=True, exist_ok=False)
    directory = folder / "run"
    directory.mkdir()
    manifest_bytes = MANIFEST.read_bytes()
    receipt = {"spec": spec, "attempt": attempt, "commit": os.environ.get("GITHUB_SHA"),
               "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
               "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
               "request_sha256": hashlib.sha256(request_file.read_bytes()).hexdigest(),
               "started_at": datetime.now(timezone.utc).isoformat(), "status": "failed",
               "confirmed_vulnerabilities": 0}
    rows, candidate_count, error_kind = [], 0, None
    governor = Governor(1, 100)
    exit_code = 2
    try:
        with network_lock():
            opener = build_opener(NoRedirect())
            scope = refreshed_scope(json.loads(manifest_bytes), governor, opener, receipt)
            receipt["expected_roots"] = scope.seeds()
            if len(scope.seeds()) != 24:
                raise ValueError("review coverage before changing operation")
            rows = collect(scope, governor, directory, opener, attempt, time.monotonic() + 600)
            result = analyze(load_documents(directory), library, 4)
            (directory / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            candidate_count = sum(d.get("exposure_review", {}).get("verdict") == "candidate_requires_manual_impact_review"
                                  for d in result["documents"] if isinstance(d.get("exposure_review"), dict))
            receipt["analysis_documents"] = len(result["documents"])
            receipt["status"] = "stopped" if governor.stopped.is_set() else "completed_with_skips" if any(r["sequence"] is None for r in rows) else "completed"
            exit_code = 2 if governor.stopped.is_set() else 0
    except BaseException as error:
        error_kind = type(error).__name__
    finally:
        # Recover flushed evidence if collection was interrupted before returning its list.
        log = directory / "requests.jsonl"
        if log.exists():
            rows = []
            for line in log.read_text(encoding="utf-8").splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    error_kind = error_kind or "PartialLogRecord"
                    receipt["status"], exit_code = "failed", 2
                    break
        # Count only. Never print response bodies, URLs, credentials or candidate details.
        summary = {"operation": spec["id"], "attempt": attempt, "status": receipt["status"],
                   "terms_requests": min(governor.issued, 4), "target_requests": sum(r["sequence"] is not None for r in rows),
                   "records": len(rows), "skipped": sum(r["sequence"] is None for r in rows),
                   "http_responses": sum(r["status"] > 0 for r in rows),
                   "candidates_requiring_review": candidate_count, "confirmed_vulnerabilities": 0, "error_kind": error_kind}
        receipt.update(summary)
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        (directory / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        archive = folder / "capture.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            output.add(directory, arcname="run")
        (folder / "campaign.enc").write_bytes(encrypt(archive.read_bytes(), recipient.read_bytes()))
        (folder / "public-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary))
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--recipient", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    spec = specification(args.request)
    if not args.execute:
        print(json.dumps({"operation": spec, "target_requests": 0, "maximum_target_requests_when_executed": 96}))
    elif args.library is None or args.recipient is None:
        parser.error("execution requires native library and recipient")
    else:
        raise SystemExit(run(args.request, args.library, args.recipient))
