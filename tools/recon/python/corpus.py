"""Hash-verified offline NASK corpus analysis using the local Rust/Rayon FFI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from nasklab import ROOT, MANIFEST, analyze


def load_corpus(inventory: Path) -> tuple[list[dict], dict]:
    private = (ROOT / "private").resolve()
    entries = json.loads(inventory.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or len(entries) > 500:
        raise ValueError("inventory must contain at most 500 observations")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    nask = next(p for p in manifest["programs"] if p["id"] == "nask")
    hosts = {h: t["tier"] for t in nask["tiers"] for h in t["exact_hosts"]}
    documents, index, total = [], {}, 0
    for row in entries:
        origin = row["origin"]
        host = urlsplit(origin).hostname
        if host not in hosts or origin != "https://" + host:
            raise ValueError("observation origin outside exact NASK host list")
        file = Path(row["file"]).resolve()
        if not file.is_relative_to(private) or file.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("corpus file outside private or over 4 MiB")
        body = file.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != row["sha256"]:
            raise ValueError("corpus hash mismatch")
        key = (origin, digest)
        provenance = {k: row[k] for k in ("source_url", "source_attribution", "file")}
        if key in index:
            documents[index[key]]["provenance"].append(provenance)
            continue
        total += len(body)
        if total > 32 * 1024 * 1024 or len(documents) >= 200:
            raise ValueError("corpus exceeds native document/byte budget")
        index[key] = len(documents)
        documents.append({"program": "nask", "tier": hosts[host], "origin": origin,
                          "source_url": row["source_url"], "source_attribution": row["source_attribution"],
                          "sha256": digest, "body": body.decode("utf-8", "replace"),
                          "provenance": [provenance]})
    return documents, {"input_observations": len(entries), "unique_origin_hash_documents": len(documents),
                       "duplicate_observations": len(entries)-len(documents), "unique_body_bytes": total}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=16, choices=range(1, 33))
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((ROOT / "private").resolve()):
        raise ValueError("output must remain inside private")
    docs, coverage = load_corpus(args.inventory)
    result = analyze(docs, args.library, args.threads)
    for row, doc in zip(result["documents"], docs, strict=True):
        row["provenance"] = doc["provenance"]
    result["corpus"] = coverage
    result["library_sha256"] = hashlib.sha256(args.library.read_bytes()).hexdigest()
    result["analysis_threads"] = args.threads
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({**coverage, "confirmed_vulnerabilities": 0}))


if __name__ == "__main__":
    main()
