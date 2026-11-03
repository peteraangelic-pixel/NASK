# Jednorazowy przebieg sprawdzający ekspozycję plików

Operacja przygotowana na prośbę użytkownika o pracę w Actions podczas nocy 3/4 listopada. Monitorowanie gałęzi Arena.ai zostało usunięte na jego prośbę. To osobna, jednorazowa operacja, bez harmonogramu ponawiania.

## Co jest sprawdzane

24 dokładne hosty z przejrzanego manifestu: 12 NASK, 7 CERT, 1 Gov.pl i 4 Władysławowa. mSzyfr i konfliktujący wpis CTF nadal są odłożone. Na każdy host przypadają cztery dozwolone w tej operacji ścieżki: dwa nieistniejące adresy kontrolne oraz `/.git/HEAD` i `/.env`.

Maksimum to 96 żądań do celów i cztery ponowne pobrania regulaminów: 100 żądań łącznie, jeden koordynator, 1 żądanie/s, bez ponowień. Kolejność jest etapowa i przeplata programy. Odczyt ograniczono do 64 KiB treści odpowiedzi. Brak wykonywania pobranych treści, rozbudowy pobrania repozytorium Git, używania znalezionych poświadczeń lub wysyłania formularzy.

Zestaw kończy się po wykonaniu prób albo zadziałaniu kontroli. Typowy czas samej kolejki to kilka minut, zależnie od sieci; nie ma powodu ponawiać identycznych odczytów przez wiele godzin. Pętla ma limit 10 minut, zewnętrzny limit procesu 15 minut i całego joba 25 minut.

## Kontrole

- Przed jakimkolwiek żądaniem do celu pobierz regulaminy czterech programów. Niezgodny hash, niedostępność dokumentu lub przekierowanie zatrzymuje operację. Weryfikacja daty używa Europe/Warsaw i sprawdza aktywność edycji, także po północy. Nie zmienia wersjonowanego manifestu.
- Używaj dokładnych hostów, HTTPS ze sprawdzaniem certyfikatów i bez przekierowań. Nie rozszerzaj nazw przez `www`, wildcard lub nowe subdomeny.
- HTTP 429 zatrzymuje całą kolejkę. Błąd transportu, przekierowanie, 401/403 lub 5xx odracza dalsze próby na danym hoście. Nie omijaj blokady przez zmianę adresu IP czy tożsamości klienta.
- Do wskazania kandydata wymagaj HTTP 200, pełnej krótkiej odpowiedzi, dwóch ważnych kontroli, silnej sygnatury formatu i różnicy względem odpowiedzi kontrolnych. HTML nie stanowi dowodu pliku. Normalizacja usuwa odbicie badanej ścieżki i długie ciągi hex.
- Git HEAD ma odpowiadać formatowi referencji lub hasha. Treść w stylu środowiska wymaga co najmniej dwóch przypisań i nazwy pola kojarzonej z danymi poufnymi. To wskazówka do ręcznej oceny; wartości mogą być przykładowe lub publiczne.

Żaden wynik nie jest automatycznie oznaczany jako potwierdzona luka. Sama dostępność metadanych lub pliku nie przesądza o realnym wpływie ani kwalifikacji do nagrody. Dwóch sprawdzanych formatów nie należy traktować jako pełnego audytu aplikacji.

## Implementacja i dowody

Python realizuje kolejkę, kontrolę regulaminów i przechwycenie ograniczonych treści. Rust/Rayon przez istniejące FFI klasyfikuje formaty i kontroluje odpowiedzi porównawcze. Wyniki i receipt są zapisywane także przy błędzie weryfikacji. Oprócz hasha manifestu zapisujemy commit, hash natywnej biblioteki i pliku operacyjnego.

Workflow `lab-night.yml` ma tę samą stałą grupę concurrency co poprzednia operacja sieciowa. Uruchomienie na gałęzi wymaga znacznika `[lab-night]` i zmiany pliku operacyjnego/workflow; zwykła poprawka kodu nie ponawia ruchu. Przed operacją przechodzą blokujące testy Pythona, Rusta i rzeczywistego FFI na syntetycznych fixture'ach.

Actions przechowuje jedynie zaszyfrowany artefakt oraz podsumowanie liczbowe przez 7 dni. Prywatny klucz pozostaje lokalnie. Pełne odpowiedzi i adresy kandydatów nie są wypisywane do logów ani commitowane. Potencjalne poświadczenia nie są sprawdzane u wystawców.

To ograniczony test integracyjny opracowanego w repo narzędzia na systemach objętych programami. Nadal obowiązują [warunki Actions](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions) oraz [GitHub AUP](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies#5-site-access-and-safety); istnienie wcześniejszych workflowów Kaggle nie stanowi podstawy do dowolnego użycia runnerów.

Podgląd operacji bez ruchu sieciowego:

```sh
python tools/recon/python/night.py --request tools/recon/night-request.json
```

## Wynik rzeczywistego przebiegu

[Operacja 41734282345](https://github.com/peteraangelic-pixel/NASK/actions/runs/41734282345) zakończyła się powodzeniem technicznym w 2 minuty 21 sekund na commicie `93f84ba482747d92e0e9d528923cde0a278773bc`. Status danych: `completed_with_skips`, czyli częściowe pokrycie. Operacja jest zakończona; nie działa nocna pętla powtórzeń ani monitor gałęzi.

[CI tego samego commitu](https://github.com/peteraangelic-pixel/NASK/actions/runs/41734282374) sprawdziło Linux i Windows: 19 testów Pythona, 8 testów Rusta oraz rzeczywiste FFI. Przed uruchomieniem operacji przeszło także [CI wersji kodu c3d0ea2](https://github.com/peteraangelic-pixel/NASK/actions/runs/41733997190).

| Etap | Faktycznie wysłane żądania |
| --- | ---: |
| Pobranie i porównanie regulaminów | 4 |
| Pierwszy adres kontrolny | 24 |
| Drugi adres kontrolny | 18 |
| Git HEAD | 18 |
| Plik środowiska | 11 |
| Razem | 75 |

Wszystkie cztery regulaminy miały zgodne hashe. Do celów wysłano 71 żądań i otrzymano 68 odpowiedzi HTTP; trzy odczyty zakończyły się błędem transportu. W zapisanych 96 rekordach 25 prób oznaczono jako pominięte po wcześniejszym problemie na hoście. Nie wykonano trzech przekierowań; dziewięć odpowiedzi miało status 403. Nie stwierdzono 429. Najmniejszy odstęp rozpoczęcia żądań do celów wynosił 1,000082 s.

Zweryfikowano hashe 56 zachowanych treści. Z nich 20 dotyczyło dwóch badanych typów plików: 9 otrzymało wynik negatywny, a 11 nierozstrzygający, m.in. ze względu na brak HTTP 200 albo niepełne kontrole. Inne próby plików nie dały treści do klasyfikacji, np. po blokadzie 403. **Kandydatów do oceny wpływu: 0. Potwierdzonych podatności: 0.** To nie jest dowód braku luk, ani pełne sprawdzenie wszystkich zaplanowanych ścieżek.

Zaszyfrowany artefakt pobrano i odszyfrowano lokalnie, potwierdzono commit źródłowy, hash manifestu i treści. Dowody: ignorowany `private/night-41734282345/`, w tym `download/campaign.enc`, `decrypted/run/receipt.json` i `verification.json`. Do publicznego repo trafiły wyłącznie kod, plan oraz to podsumowanie.
