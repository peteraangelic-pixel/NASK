// rate_limit.rs — wspólny limiter tempa zgodnie z §6 pkt 2 regulaminu NASK.
//
// Regulamin: „Dopuszczalne jest użycie automatycznych narzędzi z maksymalną
// szybkością skanowania na poziomie 5 req/s”. Naruszenie może skutkować
// odrzuceniem zgłoszenia.
//
// RateLimiter gwarantuje, że między kolejnymi żądaniami upłynie co najmniej
// 200 ms (1000 ms / 5 req = 200 ms). Wspólny dla wszystkich wątków (Mutex),
// więc nawet przy Rayonie na 16 rdzeniach nie przekroczymy limitu.

use std::sync::{Mutex, Arc};
use std::time::{Duration, Instant};

/// Wspólny limiter tempa: maksymalnie 5 żądań na sekundę.
/// Użyj jednej instancji dla wszystkich wątków (Arc<RateLimiter>).
#[derive(Debug)]
pub struct RateLimiter {
    min_interval: Duration,
    last_request: Mutex<Option<Instant>>,
}

impl RateLimiter {
    /// Tworzy limiter z podanym limitem żądań na sekundę (domyślnie 5).
    pub fn new(reqs_per_second: u32) -> Self {
        let min_interval = if reqs_per_second == 0 {
            Duration::from_millis(0)
        } else {
            Duration::from_millis(1000 / reqs_per_second as u64)
        };
        RateLimiter {
            min_interval,
            last_request: Mutex::new(None),
        }
    }

    /// Domyślny limiter: 5 req/s zgodnie z regulaminem.
    pub fn default() -> Self {
        Self::new(5)
    }

    /// Czeka aż będzie można wysłać kolejne żądanie, potem zapisuje timestamp.
    /// Zwraca czas oczekiwania w ms (do celów diagnostycznych).
    pub fn wait(&self) -> u64 {
        loop {
            let mut last = self.last_request.lock().unwrap();
            match *last {
                None => {
                    *last = Some(Instant::now());
                    return 0;
                }
                Some(t) => {
                    let elapsed = t.elapsed();
                    if elapsed >= self.min_interval {
                        *last = Some(Instant::now());
                        return 0;
                    }
                    let wait = self.min_interval - elapsed;
                    drop(last);
                    std::thread::sleep(wait);
                }
            }
        }
    }
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn first_request_no_wait() {
        let limiter = RateLimiter::new(5);
        let wait = limiter.wait();
        assert_eq!(wait, 0);
    }

    #[test]
    fn second_request_waits_at_least_200ms() {
        let limiter = RateLimiter::new(5);
        limiter.wait();
        let start = Instant::now();
        let wait = limiter.wait();
        let elapsed = start.elapsed();
        assert!(wait > 0 || elapsed >= Duration::from_millis(180), "oczekiwanie za krótkie: {:?}", elapsed);
    }

    #[test]
    fn ten_req_per_second_is_100ms() {
        let limiter = RateLimiter::new(10);
        limiter.wait();
        let start = Instant::now();
        limiter.wait();
        let elapsed = start.elapsed();
        assert!(elapsed >= Duration::from_millis(90), "oczekiwanie za krótkie: {:?}", elapsed);
    }
}
