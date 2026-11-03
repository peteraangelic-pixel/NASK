# Moduły Python (uzupełnienie narzędzi Rust)

Gdzie Rust nie jest praktyczny (gotowe biblioteki do analizy JS, prostota skryptowania),
używamy Pythona — ale z **multiprocessing** na wszystkie rdzenie i, tam gdzie wydajność
ma znaczenie, z **FFI do natywnej biblioteki Rust** (`rust/native`, wywoływana przez `ctypes`).

Pliki:
* `jsminer.py` — pobiera pliki JS i wyciąga endpointy, sekrety i komentarze deweloperskie
  (`multiprocessing.Pool`, równoległość na rdzeniach).
* `ffi_native.py` — przykład wywołania `rust/native` (cdylib) przez `ctypes` +
  `multiprocessing`.
* `build-native.sh` — buduje bibliotekę Rust (`cargo build --release --lib`) i kopiuje
  do tego katalogu.

UWAGA: Tylko cele w scope hack.cert.pl.
