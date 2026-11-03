// takeover — skaner potencjalnego subdomain takeover.
// Użycie: cat subdomeny.txt | takeover [--threads N]
//
// Dla każdej subdomeny (po jednej w linii ze stdin) wykonuje żądanie HTTP i
// sprawdza odpowiedź pod kątem sygnałów conocidas usług zewnętrznych
// (GitHub Pages, Heroku, Shopify, AWS S3, Azure i inne). Jeśli usługa wygląda
// na nieprzypisaną (np. GitHub Pages 404, Heroku "No such app"), zgłasza
// potencjalny takeover do ręcznej weryfikacji.
//
// Równoległość przez Rayon — wszystkie rdzenie (Ryzen 9 5950X: 16 rdzeni /
// 32 wątki).
//
// UWAGA: Używaj TYLKO przeciwko domenom w scope hack.cert.pl.
// Potencjalne takeover zawsze weryfikuj ręcznie (np. dig CNAME <subdomena>)
// przed zgłoszeniem na hack.cert.pl.

use rayon::prelude::*;
use std::env;
use std::io::{self, BufRead, Write};
use std::time::{Duration, Instant};

use ureq;

struct Args {
    threads: usize,
}

fn parse_args() -> Args {
    let args: Vec<String> = env::args().collect();
    let mut threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
        .max(1);

    let mut i = 1;
    while i < args.len() {
        if args[i] == "--threads" {
            i += 1;
            if let Some(v) = args.get(i).and_then(|s| s.parse::<usize>().ok()) {
                threads = v;
            }
        }
        i += 1;
    }

    Args { threads }
}

struct HostResult {
    host: String,
    status: Option<u16>,
    server: String,
    service: String,
    potential: bool,
}

/// Sprawdza jedną subdomenę pod kątem sygnałów takeover.
fn check_host(host: &str) -> HostResult {
    let url = format!("http://{}", host);
    let timeout = Duration::from_secs(8);

    let response = ureq::get(&url)
        .timeout_connect(timeout)
        .call();

    let response = match response {
        Ok(r) => r,
        Err(_) => {
            return HostResult {
                host: host.to_string(),
                status: None,
                server: String::new(),
                service: String::new(),
                potential: false,
            };
        }
    };

    let status = response.status().as_u16();
    let server = response
        .header("Server")
        .unwrap_or("-")
        .to_lowercase();
    let location = response
        .header("Location")
        .unwrap_or("")
        .to_lowercase();
    let body = response.into_string().unwrap_or_default();
    let body_lower = body.to_lowercase();

    let (potential, service) = detect_takeover(status, &server, &location, &body_lower);

    HostResult {
        host: host.to_string(),
        status: Some(status),
        server,
        service,
        potential,
    }
}

/// Wykrywa conhecida usługę zewnętrzną i czy wygląda na nieprzypisaną.
fn detect_takeover(
    status: u16,
    server: &str,
    location: &str,
    body: &str,
) -> (bool, String) {
    // GitHub Pages
    if body.contains("there isn't a github pages site here")
        || location.contains("github.io")
        || server.contains("github.com")
    {
        if status == 404 {
            return (true, "GitHub Pages (prawdopodobnie nieprzypisana)".to_string());
        }
        return (false, "GitHub Pages".to_string());
    }

    // Heroku
    if body.contains("no such app") || location.contains("herokuapp.com") {
        return (true, "Heroku (prawdopodobnie nieprzypisana)".to_string());
    }

    // Shopify
    if body.contains("sorry, this shop is currently unavailable")
        || location.contains("myshopify.com")
    {
        return (true, "Shopify (prawdopodobnie nieprzypisana)".to_string());
    }

    // AWS S3
    if body.contains("nosuchbucket") || location.contains("s3.amazonaws.com") {
        if status == 404 {
            return (true, "AWS S3 (prawdopodobnie nieprzypisany bucket)".to_string());
        }
        return (false, "AWS S3".to_string());
    }

    // Azure
    if location.contains("azurewebsites.net")
        || location.contains("cloudapp.net")
        || body.contains("windowsazure.com")
    {
        return (false, "Microsoft Azure".to_string());
    }

    // Bitbucket
    if location.contains("bitbucket.io") || body.contains("bitbucket.org") {
        return (false, "Bitbucket Pages".to_string());
    }

    // GitLab
    if location.contains("gitlab.io") || body.contains("gitlab.com") {
        return (false, "GitLab Pages".to_string());
    }

    // Tumblr
    if location.contains("tumblr.com") || body.contains("tumblr.com") {
        return (false, "Tumblr".to_string());
    }

    // Zendesk
    if location.contains("zendesk.com") || body.contains("zendesk.com") {
        return (false, "Zendesk".to_string());
    }

    // Fastly
    if server.contains("fastly") || location.contains("fastly.net") {
        return (false, "Fastly".to_string());
    }

    // Netlify
    if location.contains("netlify.app") || body.contains("netlify") {
        return (false, "Netlify".to_string());
    }

    // Squarespace
    if location.contains("squarespace.com") || body.contains("squarespace") {
        return (false, "Squarespace".to_string());
    }

    // Wix
    if location.contains("wix.com") || body.contains("wix.com") {
        return (false, "Wix".to_string());
    }

    // Statuspage
    if location.contains("statuspage.io") {
        return (false, "Statuspage".to_string());
    }

    // Surge.sh
    if location.contains("surge.sh") || body.contains("surge.sh") {
        return (false, "Surge.sh".to_string());
    }

    // Cargo
    if location.contains("cargo.site") || body.contains("cargo.site") {
        return (false, "Cargo".to_string());
    }

    (false, String::new())
}

fn main() {
    let args = parse_args();

    rayon::ThreadPoolBuilder::new()
        .num_threads(args.threads)
        .build_global()
        .expect("nie można zbudować puli Rayon");

    let stdin = io::stdin();
    let hosts: Vec<String> = stdin
        .lock()
        .lines()
        .filter_map(|line| line.ok())
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.trim().to_string())
        .collect();

    eprintln!("[+] skanowanie {} subdomen na {} wątkach", hosts.len(), args.threads);
    let start = Instant::now();

    let results: Vec<HostResult> = hosts
        .par_iter()
        .map(|host| check_host(host))
        .collect();

    let mut potential: Vec<&HostResult> = results
        .iter()
        .filter(|r| r.potential)
        .collect();
    potential.sort_by(|a, b| a.host.cmp(&b.host));

    let stdout = io::stdout();
    let mut out = stdout.lock();

    for r in &results {
        let _ = writeln!(
            out,
            "{}\t{}\t{}\t{}",
            r.status.map(|s| s.to_string()).unwrap_or("-".to_string()),
            r.server,
            r.host,
            r.service
        );
    }

    eprintln!("\n=== POTENCJALNE TAKEOVER ===");
    if potential.is_empty() {
        eprintln!("brak wykrytych sygnałów takeover");
    } else {
        for r in &potential {
            eprintln!(
                "{}  {}  {}  {}",
                r.status.unwrap_or(0), r.server, r.host, r.service
            );
        }
    }

    let elapsed = start.elapsed();
    eprintln!("[+] zakończono w {:?}", elapsed);
}
