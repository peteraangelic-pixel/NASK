// common — wspólne moduły dla wszystkich narzędzi NASK bug bounty.
//
// Zapewnia:
// 1. `scope::is_in_scope(host)` — guard zakresu zgodnie z §5 regulaminu
// 2. `rate_limit::RateLimiter` — wspólny limiter 5 req/s zgodnie z §6 pkt 2 regulaminu

pub mod scope;
pub mod rate_limit;
