"""Bounded public-surface collection and local Rust FFI analysis. No exploit probes."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import ctypes
from datetime import date, datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "programs/2026-11.json"


class Scope:
    def __init__(self, manifest: dict, programs: list[str], today: date | None = None):
        self.hosts: dict[str, dict] = {}
        self.programs = []
        now = today or date.today()
        if now.isoformat() != manifest["verified_on"]:
            raise ValueError("review program terms and update manifest verification date before collection")
        for program_id in programs:
            matches = [p for p in manifest["programs"] if p["id"] == program_id]
            if len(matches) != 1:
                raise ValueError("unknown program")
            p = matches[0]
            if not date.fromisoformat(p["start_date"]) <= now <= date.fromisoformat(p["end_date"]):
                raise ValueError("edition is not active")
            self.programs.append(program_id)
            for tier in p["tiers"]:
                for host in tier["exact_hosts"]:
                    # The ctf exception conflicts with a PDF exclusion; defer it.
                    if host == "ctf.hack.cert.pl":
                        continue
                    self.hosts[host] = {"program": program_id, "tier": tier["tier"]}

    def validate(self, url: str) -> str:
        if not isinstance(url, str) or any(ord(c) <= 32 for c in url) or "\\" in url:
            raise ValueError("invalid URL")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443)
                or parsed.fragment or parsed.query or parsed.hostname not in self.hosts):
            raise ValueError("URL outside collection scope")
        return url

    def seeds(self) -> list[str]:
        # Round-robin programs rather than exhausting one program first.
        groups = [[h for h, meta in self.hosts.items() if meta["program"] == p]
                  for p in self.programs]
        return [f"https://{group[i]}/"
                for i in range(max(map(len, groups), default=0)) for group in groups if i < len(group)]


class Governor:
    """One process-wide rate and request budget shared by every worker/program."""
    def __init__(self, rps: float, requests: int):
        if not math.isfinite(rps) or not 0 < rps <= 5 or not 1 <= requests <= 100:
            raise ValueError("rps must be finite, 0<rps<=5; requests must be 1..100")
        self.gap, self.limit = 1 / rps, requests
        self.lock = threading.Lock()
        self.next_time, self.issued = 0.0, 0
        self.stopped = threading.Event()
        self.bytes = 0

    def acquire(self) -> int:
        with self.lock:
            if self.stopped.is_set() or self.issued >= self.limit:
                raise ValueError("request budget exhausted")
            time.sleep(max(0.0, self.next_time - time.monotonic()))
            self.next_time = time.monotonic() + self.gap
            self.issued += 1
            return self.issued

    def accept_body(self, size: int) -> bool:
        with self.lock:
            if self.bytes + size > 32 * 1024 * 1024:
                self.stopped.set()
                return False
            self.bytes += size
            return True


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            value = dict(attrs).get("src")
            if value:
                self.urls.append(value)


def asset_urls(url: str, body: str, scope: Scope) -> list[str]:
    parser = Scripts()
    parser.feed(body)
    result = []
    for src in parser.urls:
        target = urljoin(url, src)
        try:
            scope.validate(target)
        except ValueError:
            continue
        if urlsplit(target).hostname == urlsplit(url).hostname and target not in result:
            result.append(target)
    # Spend the small script budget on application entry points before vendor code.
    result.sort(key=lambda u: (0 if any(p in u for p in ("/app/", "/assets/index", "/pages/", "/page-"))
                               else 1 if "main" in u else 2))
    return result[:2]


def fetch(url: str, scope: Scope, governor: Governor, directory: Path, opener=None) -> dict:
    scope.validate(url)  # Validate the complete URL immediately before any request.
    row = {"source_url": url, **scope.hosts[urlsplit(url).hostname], "sequence": None,
           "started_at": datetime.now(timezone.utc).isoformat(), "status": 0,
           "error": None, "body_file": None, "redirect_followed": False}
    response = None
    try:
        sequence = governor.acquire()
        row["sequence"] = sequence
        row["started_at"] = datetime.now(timezone.utc).isoformat()
        request = Request(url, headers={"User-Agent": "NASKLab/0.1 public-surface-research", "Accept-Encoding": "identity"})
        try:
            response = (opener or build_opener(NoRedirect())).open(request, timeout=15)
        except HTTPError as error:
            response = error  # Preserve 4xx evidence; never follow redirects.
        row["status"] = response.code
        if response.geturl() != url:
            raise ValueError("unexpected redirected response")
        content_type = response.headers.get("Content-Type", "")
        row["content_type"] = content_type
        if response.code in (301, 302, 303, 307, 308):
            row["error"] = "redirect_not_followed"
        elif response.code == 429:
            row["error"] = "rate_limited_no_retry"
            governor.stopped.set()
        elif any(t in content_type.lower() for t in ("text/html", "javascript", "text/plain")):
            body = response.read(3_000_001)
            if len(body) > 3_000_000:
                row["error"] = "body_size_limit"
            elif governor.accept_body(len(body)):
                row["sha256"] = hashlib.sha256(body).hexdigest()
                name = f"{sequence:03d}-{row['sha256'][:16]}.body"
                (directory / name).write_bytes(body)
                row["body_file"], row["bytes"] = name, len(body)
            else:
                row["error"] = "run_size_limit"
    except (OSError, URLError, ValueError) as error:
        row["error"] = type(error).__name__  # No headers, tokens or response bodies in logs.
    finally:
        if response is not None:
            response.close()
    return row


def analyze(documents: list[dict], library: Path, threads: int) -> dict:
    lib = ctypes.CDLL(str(library.resolve()))
    lib.nasklab_analyze.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
    lib.nasklab_analyze.restype = ctypes.c_void_p
    lib.nasklab_free.argtypes = [ctypes.c_void_p]
    lib.nasklab_free.restype = None
    payload = json.dumps(documents, ensure_ascii=False).encode()
    if len(payload) > 64 * 1024 * 1024:
        raise ValueError("analysis input exceeds 64 MiB")
    buffer = ctypes.create_string_buffer(payload)
    result = lib.nasklab_analyze(buffer, len(payload), threads)
    if not result:
        raise RuntimeError("native analysis returned null")
    try:
        value = json.loads(ctypes.string_at(result).decode())
    finally:
        lib.nasklab_free(result)
    if "error" in value:
        raise ValueError(value["error"])
    return value


def load_documents(directory: Path) -> list[dict]:
    documents = []
    for line in (directory / "requests.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if not row.get("body_file"):
            continue
        file = (directory / row["body_file"]).resolve()
        if not file.is_relative_to(directory.resolve()):
            raise ValueError("body path escaped run directory")
        body = file.read_bytes()
        if hashlib.sha256(body).hexdigest() != row["sha256"]:
            raise ValueError("body hash mismatch")
        documents.append({**row, "body": body.decode("utf-8", errors="replace")})
    return documents


@contextmanager
def network_lock(path: Path | None = None):
    path = path or ROOT / "private/nasklab-network.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps({"pid": __import__("os").getpid(), "created_at": datetime.now(timezone.utc).isoformat()}))
    try:
        yield
    finally:
        path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--program", action="append", required=True)
        if name == "collect":
            p.add_argument("--execute", action="store_true")
            p.add_argument("--run-dir", type=Path, required=True)
            p.add_argument("--rps", type=float, default=1)
            p.add_argument("--requests", type=int, default=48)
            p.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    p = sub.add_parser("analyze")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--threads", type=int, choices=range(1, 33), default=16)
    args = parser.parse_args()
    if args.command == "analyze":
        result = analyze(load_documents(args.run_dir), args.library, args.threads)
        (args.run_dir / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"documents": len(result["documents"]), "confirmed_vulnerabilities": 0}))
        return
    scope = Scope(json.loads(MANIFEST.read_text(encoding="utf-8")), list(dict.fromkeys(args.program)))
    if args.command == "plan" or not args.execute:
        covered = {m["program"] for m in scope.hosts.values()}
        print(json.dumps({"seeds": scope.seeds(), "network_requests": 0,
                          "deferred_no_reviewed_exact_hosts": [p for p in scope.programs if p not in covered]}, indent=2))
        return
    # Actions integration has a fixed, reviewed public-surface mode, not arbitrary probes.
    env = __import__("os").environ
    if env.get("GITHUB_ACTIONS") == "true" and env.get("NASKLAB_OPERATION") != "public-surface-validation":
        raise ValueError("Actions collection requires the reviewed public-surface integration workflow")
    if not args.run_dir.resolve().is_relative_to((ROOT / "private").resolve()):
        raise ValueError("run directory must be inside the ignored private directory")
    with network_lock():
        collect(scope, args)


def collect(scope, args):
    governor = Governor(args.rps, args.requests)
    args.run_dir.mkdir(parents=True, exist_ok=False)  # Never overwrite a previous run.
    rows = []
    with (args.run_dir / "requests.jsonl").open("x", encoding="utf-8") as output:
        def record(row):
            rows.append(row)
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            # Fair root pass first; all discovered scripts share the same governor.
            for row in pool.map(lambda url: fetch(url, scope, governor, args.run_dir), scope.seeds()[:args.requests]):
                record(row)
        extras = []
        for row in rows:
            if row.get("body_file") and "text/html" in row.get("content_type", "").lower():
                body = (args.run_dir / row["body_file"]).read_text(encoding="utf-8", errors="replace")
                extras.extend(asset_urls(row["source_url"], body, scope))
        for url in dict.fromkeys(extras):
            if governor.stopped.is_set() or governor.issued >= governor.limit:
                break
            record(fetch(url, scope, governor, args.run_dir))
    print(json.dumps({"requests": governor.issued, "rows": len(rows), "confirmed_vulnerabilities": 0}))


if __name__ == "__main__":
    main()
