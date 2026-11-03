// probe — równoległe sondowanie HTTP i fingerprint technologii.
// Użycie: cat urls.txt | probe [--method GET|HEAD] [--threads N]
//
// Przykład:
//   cat subdomains.txt | probe --method HEAD
//
// Dla każdego URL (po jednym w linii ze stdin) wysyła żądanie i wypisuje:
//   STATUS  SERWER  URL  (tytuł / technologia jeśli wykryta)
//
// Równoległość przez Rayon — przydatne przy tysiącach odkrytych subdomen.
//
// UWAGA: Tylko cele w scope hack.cert.pl.

#![allow(clippy::all)]

use std::env;
use std::io::{self, BufRead, Write};
use std::time::{Duration, Instant};

use rayon::prelude::*;
use ureq;

struct Args {
    method: String,
    threads: usize,
}

fn parse_args() -> Args {
    let args: Vec<String> = env::args().collect();
    let mut method = "HEAD".to_string();
    let mut threads = available_parallelism();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--method" => {
                i += 1;
                method = args.get(i).cloned().unwrap_or_else(|| "HEAD".to_string());
            }
            "--threads" => {
                i += 1;
                threads = args
                    .get(i)
                    .and_then(|s| s.parse::<usize>().ok())
                    .unwrap_or(available_parallelism());
            }
            _ => {}
        }
        i += 1;
    }
    Args { method, threads }
}

fn available_parallelism() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
        .max(1)
}

fn probe_one(url: &str, method: &str) -> Option<(u16, String, String)> {
    let timeout = Duration::from_secs(8);
    let response = match method {
        "GET" => ureq::get(url)
            .timeout_connect(timeout)
            .call()
            .ok()?,
        "HEAD" => ureq::head(url)
            .timeout_connect(timeout)
            .call()
            .ok()?,
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

    eprintln!("[+] sondowanie {} URL na {} wątkach", urls.len(), args.threads);
    let start = Instant::now();

    let results: Vec<(u16, String, String)> = urls
        .par_iter()
        .filter_map(|url| probe_one(url, &args.method))
        .collect();

    let stdout = io::stdout();
    let mut out = stdout.lock();
    for (status, server, url) in &results {
        let _ = writeln!(out, "{}  {}  {}", status, server, url);
    }

    let elapsed = start.elapsed();
    eprintln!("[+] zakończono w {:?}", elapsed);
}
