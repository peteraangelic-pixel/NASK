# Pilot NASKLab przez GitHub Actions

Źródło: NASK codex/multi-program-lab-20261103, research/pilot-actions-2026-11-03.md

Data: 2026-11-03. Gałąź: `codex/multi-program-lab-20261103`. Potwierdzonych podatności:
**0**. Ten raport dokumentuje działającą implementację, odczyty publiczne i jakość wyników;
nie jest zgłoszeniem luki ani prognozą nagrody.

## Wykonane zamiast pozostawionych propozycji

- Zapisano wcześniejsze porównanie programów, ocenę Arena.ai, aktualne regulaminy i
  szablon zgłoszenia w commicie `2e59e5d`.
- Wdrożono Python + rzeczywiste FFI do biblioteki Rust/Rayon, wspólną kolejkę programów,
  ogranicznik tempa, kontrolę zakresu, testy i szyfrowanie wyników w commicie
  `8f02d329405928bd683179508a6a0f741862d905`.
- Przejrzano bieżące końce 16 gałęzi trzech wskazanych projektów i wybrane źródła.
- Uruchomiono integrację kolektora na publicznych stronach z Actions. Domowe łącze nie
  wysyłało żądań tej operacji do celów konkursowych.

## Przebieg i zakres

Integracja 41699930075 zakończyła się powodzeniem na `8f02d32`. CI tej wersji
sprawdziło Linux, Windows i wywołanie FFI.

Identyfikator paczki: `c935c911986e5080a2c834e731ce5191c9b7318a95803b1d82d84055f0d8ab9a`.
Receipt wiąże żądanie operacyjne, commit, manifest zakresu, paczkę kodu i bibliotekę
natywną poprzez SHA-256.

| Program | Hosty startowe | Wszystkie żądania, w tym skrypty |
| --- | ---: | ---: |
| NASK | 12 | 22 |
| CERT Polska | 7 | 17 |
| Gov.pl | 1 | 3 |
| Władysławowo | 4 | 6 |
| mSzyfr | 0 | 0 |
| Razem | 24 | 48 |

Otrzymano 46 odpowiedzi HTTP: 44 × 200, 1 × 302, 1 × 403. Dwa odczyty zakończyły się
błędem transportu. Jednego przekierowania nie wykonano. Do lokalnej analizy zachowano
45 treści odpowiedzi.

Wszystkie 24 hosty startowe mają rekord wyniku, także przy błędzie; kompletność rekordów
nie oznacza udanego pobrania każdej strony. Kolektor nie zgadywał ścieżek ani subdomen,
nie wysyłał formularzy, nie używał kont i nie wykonywał exploitów.

Limit pilota wynosił 1 żądanie/s łącznie, z dwoma workerami pod wspólnym ogranicznikiem.
Zarejestrowany najmniejszy odstęp rozpoczęcia żądań wyniósł 1 sekundę. Zweryfikowane
regulaminy pięciu programów podają 5 żądań/s; pilot celowo używa mniejszego tempa.

mSzyfr odroczono, bo manifest nie ma jeszcze osobno zweryfikowanego hosta z zakresu
wildcard. Również konfliktujący wpis CTF pozostaje odroczony. Stan regulaminów potwierdzono
ponownym pobraniem pięciu PDF; SHA-256 zgadzały się z zapisanym manifestem.

## Korekta po rzeczywistych wynikach

Pierwsza heurystyka przyznawała punkty za wzmianki o typach pól oraz `new FormData`
bez odróżniania bibliotek od aplikacji. Zawyżyła priorytet biblioteki Modernizr z Gov.pl,
która sama tworzy testową kontrolkę pliku. To przykład błędu narzędzia, nie podatności
strony.

Commit `ae5333409c69d54ba3206f3aef4b6e1d8a2f21f6` rozdziela ogólną wzmiankę FormData
od jawnej kontrolki pliku, zeruje priorytet rozpoznawalnych skryptów wsparcia przeglądarki
i nie punktuje zwykłych ścieżek statycznych. Test regresji odtwarza ten przypadek.
Schema analizy ma wersję 2.

Przeliczenie zapisanych 45 plików wykazało, że samo zerowanie punktacji pozostawiało
mylącą etykietę uploadu przy kontrolce testowej Modernizr. Dalszy commit
`f453cac8b3cb7d32e7c569f7318058d8e76bea82` zachowuje surową wzmiankę o kontrolce
jako osobne pole, a rozpoznawalnych skryptów wsparcia nie oznacza jako funkcji uploadu/
logowania aplikacji. Rozszerzono test regresji i test rzeczywistego FFI. Po zmianach nie
ponawiano odczytów stron konkursowych.

Końcowe CI 41701587605 zakończyło się powodzeniem dla Linux i Windows: 13 testów
Pythona, 5 testów Rusta i rzeczywisty test FFI na każdym systemie. Pobraną Windows DLL
uruchomiono także lokalnie. Ponowna analiza 45 plików przez Rayon z 16 wątkami przeszła
kontrolę hashy treści i regresji Modernizr; oryginalne `analysis.json` i `receipt.json`
pozostały identyczne.

Hash użytej lokalnie DLL: `596b73b67e96b74c7d0eeb8e77f1ee9a28104a45e76f074a0e2797567a2a369c`.
Hash nowej analizy: `c62f223d1c010af270bc7631962a5c54283dbf048bebef5931b8d006187d1409`.
Analizę zapisano oddzielnie jako `analysis-v2-f453cac.json`, z metadanymi w
`reanalysis-f453cac.json`. Powstało 14 dokumentów z dodatnią heurystyczną punktacją;
nie oznacza to 14 luk. Żaden dokument nie zawierał dopasowania sprawdzanego wzorca
identyfikatora AWS; nie jest to pełny audyt sekretów.

W receipcie pierwszego pilota pole `started_targets` oznaczało liczbę żądań, czyli 48,
a nie liczbę hostów. Kod poprawiono na nazwę `requests_issued`; oryginalnego receiptu nie
zmieniamy.

## Kolejka po rozpoznaniu

NASK i CERT mają pierwszeństwo równolegle w kolejce pracy, nie poprzez mnożenie
niezależnych skanerów:

1. NASK: pogłębić mapę publicznego formularza zgłaszania dezinformacji na podstawie
   już zapisanych HTML/JS. Formularz jest obiektem badań; nie prosimy o przesyłanie
   zgłoszeń dezinformacji. HIVE pozostaje bez badań wymagających logowania, ponieważ nie
   ma własnego konta badawczego.
2. CERT: przeanalizować zapisany klient `incydent.cert.pl` i dostępność funkcji
   `mwdb.cert.pl`. Jawna kontrolka uploadu/logowania jest wskazówką do mapowania przepływu,
   nie dowodem błędu.
3. Gov.pl i Władysławowo: zachować w kolejce; wynik pojedynczej strony i dwóch skryptów
   nie uzasadnia twierdzenia o braku luk.
4. mSzyfr: najpierw wskazać konkretny dozwolony host i ustalić dostęp do aplikacji.
   Sam wildcard nie tworzy listy celów do automatycznego zgadywania.

Następna użyteczna praca to odrzucanie lub potwierdzanie konkretnych hipotez na podstawie
przepływu aplikacji. Obecny kolektor nie testuje automatycznie IDOR, SQL injection, SSRF
ani przejęć domen. Ogólne listy takich klas nie są ustaleniami badawczymi.

## Dowody i odtworzenie

Actions udostępnia wyłącznie zaszyfrowany artefakt i podsumowanie liczbowe, z retencją
7 dni. Oba pobrano lokalnie. Klucz prywatny, odszyfrowane treści i pełna analiza znajdują
się pod ignorowanym `private/`; nie trafiają do publicznego commitu ani logów.

- Oryginał: `private/pilot-41699930075/decrypted/run/`.
- Zaszyfrowana kopia: `private/pilot-41699930075/download/campaign.enc`.
- Klucz pozostający lokalnie: `private/keys/lab-recipient.key`.
- Instrukcje budowania, odszyfrowania i analizy: [README narzędzia](../tools/recon/README.md).

Wyższa wydajność CPU nie podnosi limitu sieci. GPU nie jest potrzebne do tego etapu;
nie zmierzono przewagi 100–200× względem Pythona.
