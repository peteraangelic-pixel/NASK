#!/usr/bin/env bash
# Buduje natywną bibliotekę Rust wywoływaną przez Python FFI.
# Uruchom na swojej maszynie (Ryzen 9 5950X) lub w GitHub Actions.
set -euo pipefail

cd "$(dirname "$0")/../rust/native"

if ! command -v cargo >/dev/null 2>&1; then
    echo "brak cargo — zainstaluj Rusta (https://rustup.rs) na maszynie z dostępem do internetu" >&2
    exit 1
fi

cargo build --release --lib

case "$(uname -s)" in
    Linux*)   cp target/release/libnask_native.so ../python/nask_native.so ;;
    Darwin*)  cp target/release/libnask_native.dylib ../python/nask_native.dylib ;;
    MINGW*|CYGWIN*|MSYS*) cp target/release/nask_native.dll ../python/nask_native.dll ;;
    *)        echo "nieznana platforma, skopiuj plik z target/release ręcznie" >&2 ;;
esac

echo "zbudowano natywną bibliotekę w python/"
