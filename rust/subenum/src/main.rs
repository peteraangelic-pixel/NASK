// subenum — szybkie wyliczanie subdomen z risolowaniem DNS.
// Użycie: subenum <domena> <plik_slownik> [plik_wyjsciowy]
//
// Przykład:
//   subenum nask.pl subs.txt wyniki.txt
//
// Wszystkie zapytania DNS lecą równolegle na wszystkich rdzeniach dzięki Rayon.
// Idealne na Ryzen 9 5950X (16 rdzeni / 32 wątki).
//
// UWAGA: Używaj TYLKO przeciwko domenom w scope programu na hack.cert.pl.
// Guard zakresu sprawdza, czy domena nadrzędna jest na liście §5 regulaminu.

#![allow(clippy::all)]

use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::net::ToSocketAddrs;
use std::time::Instant;

use common::scope::is_in_scope;
use rayon::prelude::*;

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

fn resolve(host: &str) -> Option<String> {
    // ToSocketAddrs blokuje wątek — Rayon obsługuje to poprawnie na puli wątków.
    // Dodajemy port :80, bo to_socket_addrs wymaga adresu z portem.
    (format!("{}:80", host)).to_socket_addrs()
        .ok()?
        .next()
        .map(|addr| addr.ip().to_string())
}

fn main() -> io::Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!("użycie: subenum <domena> <plik_slownik> [plik_wyjsciowy]");
        eprintln!("przykład: subenum nask.pl subs.txt wyniki.txt");
        std::process::exit(2);
    }

    let domain = &args[1];

    // Guard zakresu §5 — domena nadrzędna musi być na liście dozwolonych hostów.
    if !is_in_scope(domain) {
        eprintln!("BŁĄD: domena '{}' nie znajduje się w zakresie §5 regulaminu NASK.", domain);
        eprintln!("Dozwolone hosty:");
        for h in common::scope::allowed_hosts() {
            eprintln!("  - {}", h);
        }
        std::process::exit(1);
    }

    let wordlist_path = &args[2];
    let output_path = args.get(3).map(|s| s.as_str());

    let start = Instant::now();
    let words = read_wordlist(wordlist_path)?;
    eprintln!("[+] słownik: {} wpisów, domena: {}", words.len(), domain);

    let hosts: Vec<String> = words
        .iter()
        .map(|w| format!("{}.{}", w, domain))
        .collect();

    // Równoległe risolowanie DNS na wszystkich rdzeniach (Rayon).
    let results: Vec<(String, String)> = hosts
        .par_iter()
        .filter_map(|host| match resolve(host) {
            Some(ip) => Some((host.clone(), ip)),
            None => None,
        })
        .collect();

    let mut results_sorted = results;
    results_sorted.sort_by(|a, b| a.0.cmp(&b.0));

    let mut out: Box<dyn Write> = match output_path {
        Some(path) => Box::new(File::create(path)?),
        None => Box::new(io::stdout()),
    };

    for (host, ip) in &results_sorted {
        writeln!(out, "{} {}", host, ip)?;
    }

    let elapsed = start.elapsed();
    eprintln!(
        "[+] znaleziono {}/{} subdomen w {:?}",
        results_sorted.len(),
        hosts.len(),
        elapsed
    );
    Ok(())
}
