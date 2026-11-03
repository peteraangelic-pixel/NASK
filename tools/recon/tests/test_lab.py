import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.error import HTTPError
from urllib.request import build_opener

MODULE = Path(__file__).resolve().parents[1] / "python/nasklab.py"
spec = importlib.util.spec_from_file_location("nasklab", MODULE)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
MANIFEST = json.loads(lab.MANIFEST.read_text(encoding="utf-8"))


def scope(programs=None):
    return lab.Scope(MANIFEST, programs or ["nask", "cert-polska", "gov-pl"], date(2026, 11, 3))


class FakeResponse(io.BytesIO):
    code = 200
    headers = {"Content-Type": "application/javascript"}

    def geturl(self):
        return "https://nask.pl/"


class FakeOpener:
    def __init__(self, code=200, data=b"fetch('/api/fixture');"):
        self.calls, self.code, self.data = [], code, data

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        response = FakeResponse(self.data)
        response.code = self.code
        if self.code >= 300:
            raise HTTPError(request.full_url, self.code, "fixture", response.headers, response)
        return response


class Controls(unittest.TestCase):
    def test_second_coordinator_cannot_run_on_same_host(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "network.lock"
            with lab.network_lock(path):
                with self.assertRaises(FileExistsError):
                    with lab.network_lock(path):
                        self.fail("second coordinator obtained the lock")
            self.assertFalse(path.exists())

    def test_exact_scope_and_complete_url(self):
        allowed = scope()
        self.assertEqual(allowed.validate("https://nask.pl/"), "https://nask.pl/")
        for url in ["http://nask.pl/", "https://www.nask.pl/", "https://nask.pl@example.invalid/",
                    "https://nask.pl.example.invalid/", "https://nask.pl:444/", "https://127.0.0.1/",
                    "https://nask.pl/?token=fixture", "https://nask.pl/#x", "https://nask.pl\\@example.invalid/",
                    "https://ctf.hack.cert.pl/", "https://foo.lab.cert.pl/", "https://nask.pl/\n"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                allowed.validate(url)

    def test_expired_edition_and_unknown_program(self):
        with self.assertRaises(ValueError):
            lab.Scope(MANIFEST, ["nask"], date(2026, 12, 1))
        with self.assertRaises(ValueError):
            scope(["unknown"])

    def test_fair_program_order_and_deferred_wildcard(self):
        seeds = scope().seeds()
        self.assertEqual([scope().hosts[lab.urlsplit(u).hostname]["program"] for u in seeds[:3]],
                         ["nask", "cert-polska", "gov-pl"])
        self.assertEqual(scope(["mszyfr"]).seeds(), [])

    def test_concurrent_workers_share_rate_and_budget(self):
        governor = lab.Governor(5, 4)
        def permit(_):
            governor.acquire()
            return time.monotonic()
        with ThreadPoolExecutor(max_workers=4) as pool:
            stamps = sorted(pool.map(permit, range(4)))
        self.assertGreaterEqual(stamps[-1] - stamps[0], 0.57)
        self.assertEqual(governor.issued, 4)
        with self.assertRaises(ValueError):
            governor.acquire()
        for value in [0, -1, 6, float("inf"), float("nan")]:
            with self.assertRaises(ValueError):
                lab.Governor(value, 4)

    def test_disallowed_url_never_reaches_transport(self):
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                lab.fetch("https://nask.pl@example.invalid/", scope(), lab.Governor(1, 1), Path(directory), opener)
        self.assertEqual(opener.calls, [])

    def test_http_error_evidence_and_429_stop(self):
        for status in (404, 429):
            with tempfile.TemporaryDirectory() as directory:
                governor = lab.Governor(1, 2)
                result = lab.fetch("https://nask.pl/", scope(), governor, Path(directory), FakeOpener(status))
                self.assertEqual(result["status"], status)
                if status == 429:
                    self.assertTrue(governor.stopped.is_set())
                    with self.assertRaises(ValueError):
                        governor.acquire()

    def test_observed_script_scope_and_size_caps(self):
        body = '<script src="/a.js"></script><script src="https://example.invalid/b.js"></script>'
        self.assertEqual(lab.asset_urls("https://nask.pl/", body, scope()), ["https://nask.pl/a.js"])
        with tempfile.TemporaryDirectory() as directory:
            result = lab.fetch("https://nask.pl/", scope(), lab.Governor(1, 1), Path(directory),
                               FakeOpener(data=b"x" * 3_000_001))
            self.assertEqual(result["error"], "body_size_limit")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_body_tampering_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            row = {"body_file": "a.body", "sha256": hashlib.sha256(b"original").hexdigest()}
            (base / "a.body").write_bytes(b"tampered")
            (base / "requests.jsonl").write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaises(ValueError):
                lab.load_documents(base)
            row["body_file"] = "../escaped.body"
            (base / "requests.jsonl").write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaises(ValueError):
                lab.load_documents(base)

    def test_redirect_does_not_contact_destination(self):
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/must-not-be-visited")
                self.end_headers()
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with self.assertRaises(HTTPError) as error:
                build_opener(lab.NoRedirect()).open(f"http://127.0.0.1:{server.server_port}/fixture")
            self.assertEqual(error.exception.code, 302)
            error.exception.close()
            self.assertEqual(seen, ["/fixture"])
        finally:
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == "__main__":
    unittest.main()
