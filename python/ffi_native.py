#!/usr/bin/env python3
"""
ffi_native — przykład wywołania natywnej biblioteki Rust (nask_native) z Pythona
przez ctypes (FFI), połączonego z multiprocessing na wielu rdzeniach.

Budowanie natywnej biblioteki (na Twoim Ryzenie lub w GitHub Actions):
    cd rust/native
    cargo build --release
    cp target/release/libnask_native.so ../../python/nask_native.so   # Linux

UWAGA: to przykład szkieletu — kompilacja i uruchomienie po Twojej stronie,
bo w tym piaskownicy nie ma narzędzia Rust (sieć blokuje rustup.rs).
"""

from __future__ import annotations

import ctypes
import os
import sys
from multiprocessing import Pool, cpu_count
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(HERE, "nask_native.so")  # Linux; na Windows .dll, macOS .dylib


def load_native():
    if not os.path.exists(LIB_PATH):
        raise FileNotFoundError(
            f"Nie znaleziono {LIB_PATH}. Najpierw zbuduj: cd rust/native && cargo build --release"
        )
    lib = ctypes.CDLL(LIB_PATH)
    lib.nask_count_pattern.argtypes = [
        ctypes.c_char_p,  # data
        ctypes.c_int64,   # len
        ctypes.c_char_p,  # pattern
        ctypes.c_int64,   # plen
        ctypes.POINTER(ctypes.c_int64),  # out
    ]
    lib.nask_count_pattern.restype = ctypes.c_int
    lib.nask_call_counter.restype = ctypes.c_int64
    return lib


def count_pattern_native(lib, data: bytes, pattern: bytes) -> int:
    out = ctypes.c_int64(0)
    rc = lib.nask_count_pattern(data, len(data), pattern, len(pattern), ctypes.byref(out))
    if rc != 0:
        raise RuntimeError("nask_count_pattern zwrócił błąd")
    return out.value


def worker(args: Tuple[bytes, bytes]) -> int:
    """Praca dla jednego procesu — ładowanie biblioteki w każdym procesie osobno."""
    lib = load_native()
    data, pattern = args
    return count_pattern_native(lib, data, pattern)


def main() -> int:
    # Przykładowe dane: duża lista plików (symulacja pobranych plików JS/odpowiedzi HTTP).
    corpus: List[bytes] = [
        b"/api/v1/users/123 /api/v2/messages secret=AKIAIOSFODNN7EXAMPLE jwt=eyJ..." * 5000,
        b"https://nask.pl/admin/config TODO: usunąć klucz AIzaSyC..." * 5000,
        b"zwykła zawartość bez wzorców" * 5000,
    ] * 20

    pattern = b"/api/v1/"

    if not os.path.exists(LIB_PATH):
        print(
            f"biblioteka {LIB_PATH} nie istnieje — uruchom przykład w trybie czysto-Pythonowym",
            file=sys.stderr,
        )
        total = sum(data.count(pattern) for data in corpus)
        print(f"wystąpień '{pattern.decode()}' (czysty Python): {total}")
        return 0

    lib = load_native()
    # Równoległe liczenie na wielu procesach (Ryzen 9 5950X — 16 rdzeni).
    with Pool(processes=max(1, cpu_count() // 2)) as pool:
        counts = pool.map(worker, [(data, pattern) for data in corpus], chunksize=1)

    total = sum(counts)
    calls = lib.nask_call_counter()
    print(f"wystąpień '{pattern.decode()}' (Rust FFI + multiprocessing): {total}")
    print(f"liczba wywołań natywnych: {calls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
