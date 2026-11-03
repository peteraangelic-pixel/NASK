// scope.rs — guard zakresu zgodnie z §5 regulaminu konkursu NASK edycja 11/2026.
//
// Lista dokładnych hostów w scope (bez wildcardów, bez subdomen poza listą):
//
// Tier 1:
//   nask.pl, dyzurnet.pl, dns.pl, oad.nask.pl, zglos-dezinformacje.nask.pl
// Tier 2:
//   bezpiecznymiesiac.pl, secure.edu.pl, bezpiecznewybory.pl, 116sos.pl,
//   pllum.org.pl, science.nask.pl, dataannotation.pllum.org.pl
//
// UWAGA: `www.nask.pl` NIE jest na liście (nask.pl przekierowuje, ale samo www
// nie jest wypisane w §5). `gitlab.snkom.nask.pl`, `nextcloud.snkom.nask.pl`,
// `zakupy.nask.pl`, `taskmanagement.nask.pl`, `secret.eadministracja.nask.pl`
// i wszystkie `*.snkom.nask.pl`, `*.ebsi.nask.pl`, `*.sp.nask.pl` są POZA
// zakresem mimo że należą do NASK. Testowanie ich to problem prawny.

use std::sync::OnceLock;

static ALLOWED_HOSTS: OnceLock<Vec<&'static str>> = OnceLock::new();

fn allowed() -> &'static Vec<&'static str> {
    ALLOWED_HOSTS.get_or_init(|| {
        vec![
            // Tier 1
            "nask.pl",
            "dyzurnet.pl",
            "dns.pl",
            "oad.nask.pl",
            "zglos-dezinformacje.nask.pl",
            // Tier 2
            "bezpiecznymiesiac.pl",
            "secure.edu.pl",
            "bezpiecznewybory.pl",
            "116sos.pl",
            "pllum.org.pl",
            "science.nask.pl",
            "dataannotation.pllum.org.pl",
        ]
    })
}

/// Czy podany host jest na liście zakresu §5 regulaminu?
/// Sprawdzamy dokładne dopasowanie (nie wildcard — regulamin nie daje wildcardu
// na nask.pl, więc `oad.nask.pl` jest dozwolony, ale `x.nask.pl` niekoniecznie).
pub fn is_in_scope(host: &str) -> bool {
    let h = host.trim().to_lowercase();
    allowed().contains(&h.as_str())
}

/// Zwraca listę wszystkich dozwolonych hostów (dla diagnostyki).
pub fn allowed_hosts() -> &'static Vec<&'static str> {
    allowed()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tier1_hosts_in_scope() {
        assert!(is_in_scope("nask.pl"));
        assert!(is_in_scope("dyzurnet.pl"));
        assert!(is_in_scope("dns.pl"));
        assert!(is_in_scope("oad.nask.pl"));
        assert!(is_in_scope("zglos-dezinformacje.nask.pl"));
    }

    #[test]
    fn tier2_hosts_in_scope() {
        assert!(is_in_scope("bezpiecznymiesiac.pl"));
        assert!(is_in_scope("secure.edu.pl"));
        assert!(is_in_scope("bezpiecznewybory.pl"));
        assert!(is_in_scope("116sos.pl"));
        assert!(is_in_scope("pllum.org.pl"));
        assert!(is_in_scope("science.nask.pl"));
        assert!(is_in_scope("dataannotation.pllum.org.pl"));
    }

    #[test]
    fn out_of_scope_hosts_rejected() {
        assert!(!is_in_scope("gitlab.snkom.nask.pl"));
        assert!(!is_in_scope("nextcloud.snkom.nask.pl"));
        assert!(!is_in_scope("zakupy.nask.pl"));
        assert!(!is_in_scope("taskmanagement.nask.pl"));
        assert!(!is_in_scope("cert.pl"));
        assert!(!is_in_scope("example.com"));
        assert!(!is_in_scope("www.nask.pl"));
    }

    #[test]
    fn case_insensitive() {
        assert!(is_in_scope("NASK.PL"));
        assert!(is_in_scope("Oad.Nask.Pl"));
    }
}
