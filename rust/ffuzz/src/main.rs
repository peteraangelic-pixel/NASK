// ffuzz — równoległy fuzzer ścieżek i parametrów HTTP.
// Użycie: ffuzz --url <URL z FUZZ> --wordlist <plik> [opcje]
//
// Przykłady:
//   ffuzz --url "https://nask.pl/FUZZ" --wordlist paths.txt
//   ffuzz --url "https://gov.pl/api/v1/users?id=FUZZ" --wordlist ids.txt --status 200,201
//   ffuzz --url "https://mszyfr.gov.pl/search?q=FUZZ" --wordlist payloads.txt --method GET --status 200,302
//
// Wszystkie żądania HTTP idą równolegle (Rayon + ureq). Dla każdego słowa ze
// słownika podmieniamy "FUZZ" w URL i sprawdzamy kod odpowiedzi.
//
// UWAGA: Używaj TYLKO przeciwko celom w scope hack.cert.pl. Nie rób DoS.

#![allow(clippy::all)]

use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::time::{Duration, Instant};

use rayon::prelude::*;

#[derive(Debug, Clone)]
struct Args {
    url: String,
    wordlist: String,
    method: String,
    statuses: Vec<u16>,
    threads: usize,
}

fn parse_args() -> Result<Args, String> {
    let args: Vec<String> = env::args().collect();
    let mut url = String::new();
    let mut wordlist = String::new();
    let mut method = "GET".to_string();
    let mut statuses: Vec<u16> = vec![200, 301, 302, 307, 403];
    let mut threads = num_cpus();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--url" => {
                i += 1;
                url = args.get(i).cloned().ok_or("--url wymaga wartości")?;
            }
            "--wordlist" => {
                i += 1;
                wordlist = args.get(i).cloned().ok_or("--wordlist wymaga wartości")?;
            }
            "--method" => {
                i += 1;
                method = args.get(i).cloned().ok_or("--method wymaga wartości")?;
            }
            "--status" => {
                i += 1;
                statuses = args
                    .get(i)
                    .cloned()
                    .ok_or("--status wymaga wartości")?
                    .split(',')
                    .filter_map(|s| s.trim().parse::<u16>().ok())
                    .collect();
                if statuses.is_empty() {
                    return Err("--status: niepoprawna lista kodów".to_string());
                }
            }
            "--threads" => {
                i += 1;
                threads = args
                    .get(i)
                    .cloned()
                    .ok_or("--threads wymaga wartości")?
                    .parse::<usize>()
                    .map_err(|_| "--threads: niepoprawna liczba")?;
            }
            _ => return Err(format!("nieznana opcja: {}", args[i])),
        }
        i += 1;
    }

    if url.is_empty() || wordlist.is_empty() {
        return Err("wymagane: --url i --wordlist".to_string());
    }
    if !url.contains("FUZZ") {
        return Err("URL musi zawierać placeholder FUZZ".to_string());
    }

    Ok(Args {
        url,
        wordlist,
        method,
        statuses,
        threads,
    })
}

fn read_wordlist(path: &str) -> io::Result<Vec<String>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    Ok(reader
        .lines()
        .filter_map(|line| line.ok())
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.trim().to_string())
        .collect())
}

fn status_match(status: u16, wanted: &[u16]) -> bool {
    wanted.iter().any(|&s| s == status) || (wanted.is_empty() && status < 400)
}

fn fuzz_one(word: &str, args: &Args) -> Option<(String, u16, usize, String)> {
    let target = args.url.replace("FUZZ", word);
    let timeout = Duration::from_secs(8);

    let result = match args.method.to_uppercase().as_str() {
        "GET" => ureq::get(&target)
            .timeout_connect(timeout)
            .call(),
        "POST" => ureq::post(&target)
            .timeout_connect(timeout)
            .send_string("application/json", "{}"),
        "HEAD" => ureq::head(&target)
            .timeout_connect(timeout)
            .call(),
        _ => return None,
    };

    let response = match result {
        Ok(r) => r,
        Err(_) => return None,
    };

    let status = response.status().as_u16();
    if !status_match(status, &args.statuses) {
        return None;
    }

    let body = response.into_string().unwrap_or_default();
    Some((target, status, body.len(), body))
}

fn main() {
    let args = match parse_args() {
        Ok(a) => a,
        Err(e) => {
            eprintln!("błąd: {}", e);
            eprintln!(
                "użycie: ffuzz --url <URL/FUZZ> --wordlist <plik>",
            );
            eprintln!(
                "       [--method GET|POST|HEAD] [--status 200,403] [--threads N]",
            );
            std::process::exit(2);
        }
    };

    let words = match read_wordlist(&args.wordlist) {
        Ok(w) => w,
        Err(e) => {
            eprintln!("błąd odczytu słownika: {}", e);
            std::process::exit(1);
        }
    };

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .expect("nie można zbudować puli Rayon");

    eprintln!(
        "[+] fuzzowanie {} wątkami, {} słów, cel: {}",
        args.threads,
        words.len(),
        args.url.replace("FUZZ", "<FUZZ>")
    );

    let start = Instant::now();
    let mut found: Vec<(String, u16, usize, String)> = words
        .par_iter()
        .filter_map(|word| fuzz_one(word, &args))
        .collect();

    found.sort_by(|a, b| a.1.cmp(&b.1).then_with(|| a.0.cmp(&b.0)));

    let stdout = io::stdout();
    let mut out = stdout.lock();
    for (target, status, body_len, _body) in &found {
        let _ = writeln!(out, "{}  {}  {}B", status, target, body_len);
    }

    let elapsed = start.elapsed();
    eprintln!(
        "[+] trafienia: {}/{} w {:?}",
        found.len(),
        words.len(),
        elapsed
    );
}

// num_cpus bez zewnętrznej zależności: odczytujemy liczbę rdzeni ze std.
fn num_cpus() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
        .max(1)
}
