# Zakres (scope) i wyłączenia — programy na hack.cert.pl

Na podstawie https://hack.cert.pl/programs i https://hack.cert.pl/programs/nask-pib/nask/editions/1

## Obowiązuje dla wszystkich programów

### ✅ W scope (do testowania)
Wszystkie typy wymienione w tabeli konkursu (01–20), m.in.:
- RCE, SSRF, SSTI, File Upload → RCE
- SQL injection, XXE
- Przejęcie konta, omijanie uwierzytelniania
- IDOR / Broken Access Control
- Mass Assignment
- XSS (poza wyłączeniami)
- Open Redirect (w OAuth/OIDC lub łańcuchu ataku)
- HTTP Request Smuggling, Web Cache Poisoning

### ❌ Poza scope (nie testować!)
- Ataki wymagające konta pracownika NASK / specjalnych uprawnień AD
- Ataki wymagające MITM, fizycznego dostępu, DevTools
- Wyciek wersji oprogramowania, stack trace, IP, user enumeration (bez dalszego wpływu)
- Brak nagłówków bezpieczeństwa, HSTS, captchy, flag security w ciasteczkach
- Brak SPF/DKIM/DMARC (jeśli nie umożliwia spoofingu)
- Wygasłe certyfikaty SSL bez realnego scenariusza ataku
- Otwarte porty bez znaczenia bezpieczeństwa
- Nieaktualne oprogramowanie/biblioteki bez wpływu
- Znane CVE bez działającego PoC
- Ataki frontendowe działające tylko po stronie użytkownika, nie pozwalające na uruchomienie kodu u innych osób

### 🚫 Zabronione
- Ataki typu DoS / zagrożenie ciągłości działania usług państwowych
- Testowanie poza zakresem programu
- Ujawnianie luki publicznie przed wdrożeniem poprawki

---

## Programy w edição 11/2026

| Program | Nagroda maksymalna | Uwagi |
|---------|-------------------|-------|
| NASK (nask-pib) | 20 000 PLN | Główny cel — instytut badawczy NASK |
| CERT Polska | 20 000 PLN | Zespół reagowania na incydenty |
| Portal Gov.pl | 20 000 PLN | Rządowy portal usług publicznych |
| mSzyfr | 20 000 PLN | Rządowy komunikator — warto sprawdzić API |
| Gmina Władysławowo | 4 000 PLN | Łatwiejszy cel na rozgrzewkę |

Pula nagród całego programu: **1 000 000 PLN**.
