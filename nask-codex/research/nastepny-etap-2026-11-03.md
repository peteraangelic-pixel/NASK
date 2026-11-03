# Następny etap po przeglądzie badań

Źródło: NASK codex/multi-program-lab-20261103, research/nastepny-etap-2026-11-03.md

Stan: 2026-11-03. Program: NASK, edycja 11/2026.

## Decyzja

Pierwsza funkcja do pogłębienia: bezpieczeństwo publicznego formularza
`zglos-dezinformacje.nask.pl` (Tier 1). Nie chodzi o wyszukiwanie i zgłaszanie
dezinformacji, lecz o badanie aplikacji objętej programem NASK. HIVE
`dataannotation.pllum.org.pl` (Tier 2) odkładamy w części wymagającej logowania:
użytkownik nie ma konta ani związku z zespołem projektu, a dostęp według przekazanej
informacji jest zaproszeniowy. Nie wymagamy zakładania konta w HIVE. Konto na platformie
blockchain `signup.hive.io` nie daje dostępu do aplikacji NASK.

Ta kolejność wynika z faktycznie widocznego przepływu i dostępności. Nie oznacza, że
znaleziono podatność albo zmierzono szansę wygranej.

## Już wykonane

- Odczytano publiczny formularz i ekran logowania HIVE.
- Pobranie i analiza offline dwóch skryptów publicznych dały rzeczywisty opis sposobu
  wysyłania formularza i mapę części routingu HIVE.
- Zweryfikowano, że zwykłe wejście na ścieżkę rejestracji z kodu HIVE wraca do logowania.
- Porównano nowy commit Arena.ai z poprzednim i uruchomiono sprawdzenie kompilacji jego
  nowego skanera.
- Sprawdzono kompletność dostarczonych logów i próbowano uruchomić testy drugiego narzędzia.
  Lokalny brak linkera blokuje ich wykonanie; nie oznaczono ich jako zaliczonych.

## Proponowana sesja badawcza

1. **Do 45 minut: mapa jednego przepływu.** Na podstawie publicznego kodu klienta opisać
   pola formularza, walidację, sposób przesyłania pliku i prezentację odpowiedzi. Oddzielić
   obserwacje klienta od hipotez o serwerze. Bez wymyślania paneli administracyjnych czy
   endpointów niezaobserwowanych w aplikacji.
2. **Do 45 minut: 3-5 hipotez z warunkami odrzucenia.** Priorytetem są konkretne granice,
   np. walidacja pliku i sposób jego późniejszego udostępnienia, jeśli aplikacja ujawnia
   taki przepływ. Sam fakt pola URL nie dowodzi pobierania jego treści przez serwer, a
   samo przyjęcie pliku nie dowodzi zagrożenia. Każda ewentualna próba wymaga minimalnego
   niezakłócającego dowodu opartego na własnych danych.
3. **Do 30 minut: decyzja o kontynuacji.** Gdy pozostają tylko ogólne przypuszczenia,
   zmienić funkcję lub serwis. Jeśli jest konkretny sygnał, przygotować odtwarzalny dowód,
   sprawdzić aktualny regulamin, rzeczywisty wpływ i wyłączenia. Dopiero wtedy powstaje
   szkic zgłoszenia; nagroda i CVSS pozostają do oceny.

Wysłanie testowego formularza tworzy zgłoszenie u organizacji; na etapie rozpoznania nie
wykonano tej czynności. Nie kopiujemy zaleceń innych AI o wysyłaniu wiadomości jako
automatycznej zgody użytkownika.

## Narzędzia

Nie budować kolejnych skanerów klas podatności. Z paczki z Dysku warto adaptować analizę
lokalną w Rust + Rayon i pomysł kontroli catch-all. Wspólną warstwę HTTP należy dopiero
poprawić i zweryfikować, zanim użyje jej automatyzacja.

Minimalne wymagania przy implementacji: dokładne hosty, kontrola złożonego URL, wyłączone
przekierowania, limit 1 żądanie/s dla początkowej pracy, ograniczony rozmiar i czas
odpowiedzi, jawne błędy, rejestr żądań z czasem i identyfikatorem przebiegu. Dane własnych
sesji i potencjalne sekrety pozostają poza publicznymi logami.

Nowy generator raportów Arena.ai może posłużyć jako inspiracja do formatu. Skaner takeover
nie jest gotowy do użycia; dodany commit nie naprawił wcześniejszych błędów narzędzi i CI.

## Wynik tego etapu

Powstała zweryfikowana mapa wejścia do badań i ocena przydatności materiałów.
Potwierdzonych podatności: 0. Poprawki narzędzi i powyższa sesja pogłębionych badań są
propozycją dalszej pracy, nie wykonanymi testami.
