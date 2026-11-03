# NASKLab: multi-program surface triage

Python controls the request queue and calls a Rust cdylib through ctypes. Rust uses a dedicated Rayon pool for CPU work. Network I/O has 1-4 threads with a shared rate limiter; adding processes or runners does not increase the authorized rate. GPU processing is not needed for this workload.

This is a first-stage triage tool. It collects public pages and up to two already-linked first-party scripts per page, identifies authentication/upload surfaces, and extracts route literals with their source URL. It does not confirm vulnerabilities, run exploit payloads, submit forms, enumerate accounts, access private resources, or assign CVSS scores. Automated results need further interpretation and a reproducible proof of real impact.

## Current coverage

The reviewed manifest contains exact hosts for NASK, CERT Polska, Gov.pl and Władysławowo. Unlisted `www` names are not implicit aliases. Wildcards do not cause enumeration. mSzyfr has no individually reviewed exact subdomain in this version, so it is deferred. The conflicting `ctf.hack.cert.pl` entry is also deferred. The program and edition must be active, and the manifest's verification date must be today's date.

Requests are ordered round-robin across programs. One process coordinates all workers, and an exclusive local lock prevents starting a second coordinator from the same checkout. Default rate: 1 request/s total; absolute CLI maximum: 5. Never run parallel copies from separate checkouts, hosts, other AI tools or workflows without a common aggregate limit.

## Offline preview (no target requests)

```sh
python tools/recon/python/nasklab.py plan --program nask --program cert-polska --program gov-pl --program wladyslawowo --program mszyfr
```

## Collection and the reviewed integration workflow

Use a host/provider that permits the intended work. Confirm current program terms and host lists first. The included Actions operation is limited to validating this collector on public pages and their linked scripts; it is not an arbitrary attack job.

```sh
python tools/recon/python/nasklab.py collect --program nask --program cert-polska --program gov-pl --program wladyslawowo --run-dir private/runs/first-pass --requests 48 --rps 1 --workers 2 --execute
```

Without `--execute`, collection prints a preview only. Under `GITHUB_ACTIONS=true`, the reviewed `NASKLAB_OPERATION=public-surface-validation` integration mode is required. Redirects are not followed, TLS validation remains enabled, and query strings, credentials, fragments and non-443 ports are rejected. A 429 stops further scheduled requests without retry; already-started requests can finish. Bodies are capped at 3 MB each and 32 MiB total. Results preserve HTTP error statuses and record size/transport failures. HTML/script bodies and request metadata go only under the ignored `private/` directory. No session cookies or authorization headers are supplied.

The exclusive lock is `private/nasklab-network.lock`. If a process is killed, verify its recorded PID is no longer active before removing its stale lock. The lock coordinates one checkout, not independent machines.

## Local analysis with Rust FFI

```sh
cargo build --locked --release --manifest-path tools/recon/Cargo.toml
python tools/recon/python/nasklab.py analyze --run-dir private/runs/first-pass --library tools/recon/target/release/libnasklab.so --threads 16
```

On Windows the library is `tools/recon/target/release/nasklab.dll`. GitHub CI builds both Linux and Windows native libraries and tests actual FFI calls on synthetic data. Artifacts contain binaries only. The local machine needs a compatible native runtime to load the Windows DLL.

`analysis.json` preserves source URLs and hashes. Its score prioritizes application surfaces, not exploitability or expected money. A matching identifier is masked and remains unconfirmed. Route literals can themselves contain information, so treat the entire result as private. A route seen in JavaScript does not authorize probing a different host or prove the route is live.

Analysis schema v2 distinguishes an explicit file control from a generic FormData mention. Recognizable browser-support scripts receive no priority points; ordinary static/navigation routes do not inflate the score. These are conservative triage heuristics: bundled code can still contain inactive controls, and filename hints do not reliably identify every vendor bundle.

## Verification

```sh
python -m unittest discover -s tools/recon/tests -p test_lab.py -v
cargo test --locked --manifest-path tools/recon/Cargo.toml
python tools/recon/tests/ffi_smoke.py --library tools/recon/target/release/libnasklab.so
```

Tests cover scope/URL boundary errors, expiry, cross-program ordering, rate and request budgets across workers, one-coordinator locking, redirects using a loopback fixture, HTTP error evidence, body limits, evidence tampering, native source attribution, masking and FFI allocation/error handling. These tests do not contact competition targets.

## Actions and policy

`lab-ci.yml` builds/tests our software on synthetic and loopback fixtures. `lab-campaign.yml` adds an opt-in, bounded integration validation of this project's collector: reviewed public landing pages, linked first-party scripts, no exploit probes or state-changing requests. It tests controls and evidence handling as part of development of this repository's software. [GitHub's additional Actions terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions) and [acceptable-use policy](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies#5-site-access-and-safety) both apply; the historical existence of other workflows is not evidence that any arbitrary use is permitted.

The request file has a unique operation ID and fixed reviewed fields. Like the ARC operations workflow, a push with `[lab-surface]` starts the operation before a new workflow has been registered on the default branch. All network operations share the fixed `nasklab-network-single-coordinator` concurrency group. Never shard network work into runners with independent rate limiters. CPU-only analysis can be parallelized separately.

The pilot request covers up to 48 requests at 1 request/s total with two I/O workers. It does not probe vulnerabilities. A receipt binds the exact code, library, scope manifest and request; missing or duplicate root records fail the completeness check. Transport errors remain errors and are counted separately from coverage. No auto-commit of raw results is permitted.

## Encrypted artifacts

The recipient public key is `tools/recon/recipient.pub`. Its private key is generated locally under `private/keys/` and is never uploaded. Actions archives the private run directory and encrypts it with a fresh Fernet key wrapped using RSA-OAEP-SHA256. Only the envelope and a count-only summary are uploaded for seven days. Keep the private key and downloaded evidence safe; without the private key the envelope cannot be decrypted.

```sh
python tools/recon/python/evidence.py decrypt --private private/keys/lab-recipient.key --input private/downloaded/campaign.enc --output private/downloaded/campaign.tar.gz
```

Decrypt only artifacts from the verified repository, commit and workflow run. Encryption protects the contents, not the sender's identity. Check the receipt and hashes before using the results. Raw decrypted results remain local.

Raw research, run directories, private keys and unannounced findings are excluded from public Git history. Review changes before committing; `.gitignore` alone does not prevent an explicit forced add or content pasted into a tracked file.
