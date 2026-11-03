// nask_native — natywna biblioteka C wywoływana z Pythona przez ctypes/FFI.
//
// Przykład zastosowania: szybkie szukanie wzorców (sekretów, endpointów, sygnatur
// podatności) w dużych zbiorach plików JS/odpowiedzi HTTP. Krytyczny odcinek w
// Rustu, równoległość w Pythonie przez multiprocessing.Pool na 16 rdzeniach
// (Ryzen 9 5950X).

#![allow(clippy::all)]

use std::slice;
use std::sync::atomic::{AtomicUsize, Ordering};

/// Liczy wystąpienia wzorca `pattern` w buforze `data`.
/// Zapisuje wynik w `out` i zwraca 0 przy sukcesie, -1 przy błędnych argumentach.
#[no_mangle]
pub unsafe extern "C" fn nask_count_pattern(
    data: *const u8,
    len: i64,
    pattern: *const u8,
    plen: i64,
    out: *mut i64,
) -> i32 {
    if data.is_null() || pattern.is_null() || out.is_null() {
        return -1;
    }
    let data = unsafe { slice::from_raw_parts(data, len as usize) };
    let pattern = unsafe { slice::from_raw_parts(pattern, plen as usize) };

    let count: i64 = if plen == 0 || plen > len as usize {
        0
    } else {
        data.windows(plen as usize)
            .filter(|window| window == pattern)
            .count() as i64
    };

    unsafe { *out = count };
    0
}

/// Liczy wystąpienia wzorca w wielu buforach jednocześnie (Równoległość Rayon w Rustu).
/// `data_ptrs` — tablica wskaźników, `lens` — długości, `pattern` — wspólny wzorzec.
/// Wyniki zapisywane są do tablicy `outs` tej samej długości co dane wejściowe.
#[no_mangle]
pub unsafe extern "C" fn nask_count_pattern_batch(
    data_ptrs: *const *const u8,
    lens: *const i64,
    count: i64,
    pattern: *const u8,
    plen: i64,
    outs: *mut i64,
) -> i32 {
    if data_ptrs.is_null() || lens.is_null() || pattern.is_null() || outs.is_null() {
        return -1;
    }

    let data_ptrs = unsafe { slice::from_raw_parts(data_ptrs, count as usize) };
    let lens = unsafe { slice::from_raw_parts(lens, count as usize) };
    let pattern = unsafe { slice::from_raw_parts(pattern, plen as usize) };
    let outs = unsafe { slice::from_raw_parts_mut(outs, count as usize) };

    let results: Vec<i64> = (0..count as usize)
        .into_par_iter()
        .map(|i| unsafe {
            let data = slice::from_raw_parts(*data_ptrs.get_unchecked(i), *lens.get_unchecked(i) as usize);
            if plen == 0 || plen as usize > data.len() {
                0
            } else {
                data.windows(plen as usize)
                    .filter(|w| w == pattern)
                    .count() as i64
            }
        })
        .collect();

    for (i, c) in results.into_iter().enumerate() {
        unsafe { *outs.get_unchecked_mut(i) = c };
    }
    0
}

/// Atomowy licznik wywołań — pomocniczy do statystyk z wielu procesów Pythona.
static CALL_COUNTER: AtomicUsize = AtomicUsize::new(0);

#[no_mangle]
pub unsafe extern "C" fn nask_call_counter() -> i64 {
    CALL_COUNTER.fetch_add(1, Ordering::Relaxed) as i64
}
