#!/usr/bin/env python3
"""
jsminer — pobiera pliki JS z podanych URL i wyciąga z nich:
  * endpointy API (ścieżki zaczynające się od /api, /v1, /v2 itp.),
  * pełne adresy URL (https://...),
  * możliwe sekrety/klucze API (regexy: AWS keys, GitHub pat, Google AIza, sk_live, JWT-ish),
  * komentarze deweloperskie (TODO, FIXME, BUG, HACK, XXX, SECRET).

Działa na wiele procesów (multiprocessing.Pool) — wykorzystuje wszystkie rdzenie
Ryzen 9 5950X. Krytyczne operacje (liczenie wystąpień wzorców w dużych plikach)
można przenieść do natywnej biblioteki Rust przez FFI (moduł ffi_native).

UWAGA: Używaj TYLKO przeciwko celom w scope hack.cert.pl.

Przykład:
    cat urls.txt | python3 python/jsminer.py --workers 16 --out results.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from multiprocessing import Pool, cpu_count
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Iterable, List, Dict, Any

# --- wzorce do wykrywania ---------------------------------------------------

ENDPOINT_RE = re.compile(r"""(?:
    ["'](?P<path>/(?:api|v[0-9]+|rest|graphql|auth|oauth|sso|admin|user|users|message|messages|file|upload|download|config|settings|webhook|internal|private|debug|swagger|openapi)[^"']*)["']
)|(?P<url>https?://[^"'\\]+)
""", re.VERBOSE)

SECRET_RE = re.compile(r"""(?:
    (?:api[_-]?key|apikey|secret|token|password|passwd|pwd|access[_-]?token|private[_-]?key)[\s'":]{0,10}(["'])([^"']{6,})\1
)|(?:
    (?:AKIA[0-9A-Z]{16})                                 # AWS access key
  | (?:sk_live_[0-9a-zA-Z]{24})                          # Stripe live key
  | (?:sk_test_[0-9a-zA-Z]{24})                          # Stripe test key
  | (?:AIza[0-9A-Za-z_\-]{35})                           # Google API key
  | (?:github_pat_[0-9a-zA-Z_]{20,})                     # GitHub PAT
  | (?:eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)  # JWT-ish
)
""", re.VERBOSE | re.IGNORECASE)

COMMENT_RE = re.compile(r"""(?:
    //\s*(?:TODO|FIXME|BUG|HACK|XXX|SECRET|PASSWORD|TOKEN|KEY)[^\n]*
)|(?:
    /\*.*?(?:TODO|FIXME|BUG|HACK|XXX|SECRET|PASSWORD|TOKEN|KEY).*?\*/
)
""", re.VERBOSE | re.DOTALL | re.IGNORECASE)

TIMEOUT_S = 10
UA = "NASK-JSMiner/0.1 (bug-bounty recon; scope hack.cert.pl only)"


def fetch(url: str) -> str:
    """Pobiera zawartość URL jako tekst (bez rzucania wyjątków na błędy sieci)."""
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=TIMEOUT_S) as resp:
            data = resp.read(2_000_000)  # max 2 MB na plik
            return data.decode("utf-8", errors="replace")
    except (HTTPError, URLError, OSError, ValueError):
        return ""
    except Exception:
        return ""


def extract(text: str, source: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for m in ENDPOINT_RE.finditer(text):
        val = m.group("path") or m.group("url") or ""
        findings.append({"type": "endpoint", "value": val, "source": source})
    for m in SECRET_RE.finditer(text):
        findings.append({"type": "secret", "value": m.group(0)[:120], "source": source})
    for m in COMMENT_RE.finditer(text):
        findings.append({"type": "comment", "value": m.group(0)[:200].replace("\n", " "), "source": source})
    return findings


def process_one(url: str) -> Dict[str, Any]:
    """Jednostka pracy dla multiprocessing.Pool."""
    text = fetch(url)
    findings = extract(text, url) if text else []
    return {
        "url": url,
        "fetched": bool(text),
        "bytes": len(text),
        "findings": findings,
    }


def iter_urls(source: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for line in source:
        u = line.strip()
        if not u or u.startswith("#"):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Wyciąganie endpointów i sekretów z plików JS (multiprocessing)")
    parser.add_argument("file", nargs="?", help="plik z URL (po jednym w linii) — domyślnie stdin")
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() // 2),
                        help="liczba procesów roboczych (domyślnie połowa rdzeni)")
    parser.add_argument("--out", help="plik wyjściowy JSONL (domyślnie stdout)")
    args = parser.parse_args()

    source: Iterable[str]
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            source = fh
    else:
        source = sys.stdin

    urls = iter_urls(source)
    if not urls:
        print("brak URL do przetworzenia", file=sys.stderr)
        return 1

    print(f"[+] {len(urls)} URL, {args.workers} procesów", file=sys.stderr)

    out_stream = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout

    # Równoległe pobieranie i analizowanie na wielu rdzeniach.
    with Pool(processes=args.workers) as pool:
        for result in pool.imap_unordered(process_one, urls, chunksize=1):
            out_stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            out_stream.flush()

    if args.out:
        out_stream.close()
    print(f"[+] zakończono", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
