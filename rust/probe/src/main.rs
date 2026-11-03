// probe — równoległe sondowanie HTTP i fingerprint technologii.
// Użycie: cat urls.txt | probe [--method GET|HEAD] [--threads N] [--rps 5]
//
// Przykład:
//   cat subdomains.txt | probe --method HEAD
//   echo "https://oad.nask.pl/" | probe --method GET
//
// Dla każdego URL (po jednym w linii ze stdin) wysyła żądanie i wypisuje:
//   STATUS  SERWER  URL
//
// Równoległość przez Rayon, ale z WSPÓLNYM rate limiterem 5 req/s
// zgodnie z §6 pkt 2 regulaminu NASK.
// Guard zakresu §5 — żądania do hostów poza listą są pomijane, nie wysyłane.
//
// UWAGA: Tylko cele w scope hack.cert.pl.

#![allow(clippy::all)]

use std::env;
use std::io::{self, BufRead, Write};
use std::time::{Duration, Instant};

use common::rate_limit::RateLimiter;
use common::scope::is_in_scope;
use rayon::prelude::*;
use ureq;

struct Args {
    method: String,
    threads: usize,
    rps: u32,
}

fn parse_args() -> Args {
    let args: Vec<String> = env::args().collect();
    let mut method = "HEAD".to_string();
    let mut threads = available_parallelism();
    let mut rps = 5u32; // domyślnie 5 req/s zgodnie z regulaminem

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--method" => {
                i += 1;
                method = args
                    .get(i)
                    .cloned()
                    .unwrap_or_else(|| "HEAD".to_string());
            }
            "--threads" => {
                i += 1;
                threads = args
                    .get(i)
                    .and_then(|s| s.parse::<usize>().ok())
                    .unwrap_or(available_parallelism());
            }
            "--rps" => {
                i += 1;
                rps = args
                    .get(i)
                    .and_then(|s| s.parse::<u32>().ok())
                    .unwrap_or(5);
                if rps == 0 || rps > 5 {
                    eprintln!("ostrzeżenie: regulamin dopuszcza max 5 req/s, ustawiam 5");
                    rps = 5;
                }
            }
            _ => {}
        }
        i += 1;
    }
    Args { method, threads, rps }
}

fn available_parallelism() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
        .max(1)
}

/// Wyodrębnia host z URL (http://host/path lub https://host/path).
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

fn probe_one(url: &str, method: &str, agent: &ureq::Agent, limiter: &RateLimiter) -> Option<(u16, String, String)> {
    // Guard zakresu §5 — sprawdź host ZANIM wyślesz jakiekolwiek żądanie.
    let host = match extract_host(url) {
        Some(h) => h,
        None => return None,
    };
    if !is_in_scope(&host) {
        eprintln!("[scope] pominięto poza zakresem: {}", host);
        return None;
    }

    // Rate limiter §6 pkt 2 — max 5 req/s, wspólny dla wszystkich wątków.
    limiter.wait();

    let timeout = Duration::from_secs(8);
    let response = match method {
        "GET" => agent.get(url).call().ok()?,
        "HEAD" => agent.head(url).call().ok()?,
        _ => return None,
    };

    let status = response.status().as_u16();
    let server = response
        .header("Server")
        .unwrap_or_else(|| response.header("server").unwrap_or("-"))
        .to_string();

    Some((status, server, url.to_string()))
}

fn main() {
    let args = parse_args();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .expect("nie można zbudować puli Rayon");

    let stdin = io::stdin();
    let urls: Vec<String> = stdin
        .lock()
        .lines()
        .filter_map(|line| line.ok())
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.trim().to_string())
        .collect();

    // JEDEN wspólny limiter dla wszystkich wątków (Arc wäre idealne, ale
    // prostsze: przekazujemy referencję — par_iter nie pozwala na mutable
    // shared state, więc używamy Mutex wewnątrz RateLimiter).
    let limiter = RateLimiter::new(args.rps);
    let agent = build_agent(Duration::from_secs(8));

    eprintln!(
        "[+] sondowanie {} URL na {} wątkach, limit {} req/s",
        urls.len(),
        args.threads,
        args.rps
    );
    let start = Instant::now();

    // par_iter wymaga &self — RateLimiter.wait() przyjmuje &self, więc działa.
    let results: Vec<(u16, String, String)> = urls
        .par_iter()
        .filter_map(|url| probe_one(url, &args.method, &agent, &limiter))
        .collect();

    let stdout = io::stdout();
    let mut out = stdout.lock();
    for (status, server, url) in &results {
        let _ = writeln!(out, "{}  {}  {}", status, server, url);
    }

    let elapsed = start.elapsed();
    eprintln!("[+] zakończono w {:?}", elapsed);
}
