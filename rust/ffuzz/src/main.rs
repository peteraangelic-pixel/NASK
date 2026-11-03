// ffuzz — równoległy fuzzer ścieżek i parametrów HTTP.
// Użycie: ffuzz --url <URL z FUZZ> --wordlist <plik> [opcje]
//
// Przykłady:
//   ffuzz --url "https://oad.nask.pl/FUZZ" --wordlist paths.txt
//   ffuzz --url "https://zglos-dezinformacje.nask.pl/api/FUZZ" --wordlist endpoints.txt --method GET --status 200,403
//
// Wszystkie żądania HTTP idą równolegle (Rayon + ureq) ALE z WSPÓLNYM
// rate limiterem 5 req/s zgodnie z §6 pkt 2 regulaminu NASK.
// Guard zakresu §5 — host z URL musi być na liście dozwolonych.
//
// UWAGA: Używaj TYLKO przeciwko celom w scope hack.cert.pl. Nie rób DoS.
// Przy 5 req/s i słownikiem 1000 słów = ok. 3,5 minuty — celowo wolno,
// żeby nie naruszyć regulaminu.

#![allow(clippy::all)]

use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::time::{Duration, Instant};

use common::rate_limit::RateLimiter;
use common::scope::is_in_scope;
use rayon::prelude::*;
use ureq;

#[derive(Debug, Clone)]
struct Args {
    url: String,
    wordlist: String,
    method: String,
    statuses: Vec<u16>,
    threads: usize,
    rps: u32,
}

fn parse_args() -> Result<Args, String> {
    let args: Vec<String> = env::args().collect();
    let mut url = String::new();
    let mut wordlist = String::new();
    let mut method = "GET".to_string();
    let mut statuses: Vec<u16> = vec![200, 301, 302, 307, 403];
    let mut threads = num_cpus();
    let mut rps = 5u32;

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
            "--rps" => {
                i += 1;
                rps = args
                    .get(i)
                    .cloned()
                    .ok_or("--rps wymaga wartości")?
                    .parse::<u32>()
                    .map_err(|_| "--rps: niepoprawna liczba")?;
                if rps > 5 {
                    eprintln!("ostrzeżenie: regulamin max 5 req/s, ustawiam 5");
                    rps = 5;
                }
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
        rps,
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

/// Wyodrębnia host z URL dla guardu zakresu.
fn extract_host(url: &str) -> Option<String> {
    let rest = url.strip_prefix("http://").or_else(|| url.strip_prefix("https://"))?;
    let host_end = rest.find('/').unwrap_or(rest.len());
    Some(rest[..host_end].to_string())
}

/// Buduje ureq::Agent z timeoutem connect (poprawne API dla ureq 2.x).
fn build_agent(timeout: Duration) -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_connect(timeout)
        .build()
}

fn fuzz_one(word: &str, args: &Args, agent: &ureq::Agent, limiter: &RateLimiter) -> Option<(String, u16, usize, String)> {
    let target = args.url.replace("FUZZ", word);

    // Guard zakresu §5 — sprawdź host PRZED żądaniem.
    let host = match extract_host(&target) {
        Some(h) => h,
        None => return None,
    };
    if !is_in_scope(&host) {
        return None;
    }

    // Rate limiter §6 pkt 2 — max 5 req/s.
    limiter.wait();

    let timeout = Duration::from_secs(8);
    let result = match args.method.to_uppercase().as_str() {
        "GET" => agent.get(&target).call(),
        "POST" => agent.post(&target).send_string("application/json", "{}"),
        "HEAD" => agent.head(&target).call(),
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
                "       [--method GET|POST|HEAD] [--status 200,403] [--threads N] [--rps 5]",
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

    let limiter = RateLimiter::new(args.rps);
    let agent = build_agent(Duration::from_secs(8));

    eprintln!(
        "[+] fuzzowanie {} wątkami, {} słów, limit {} req/s, cel: {}",
        args.threads,
        words.len(),
        args.rps,
        args.url.replace("FUZZ", "<FUZZ>")
    );

    let start = Instant::now();
    let mut found: Vec<(String, u16, usize, String)> = words
        .par_iter()
        .filter_map(|word| fuzz_one(word, &args, &agent, &limiter))
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
