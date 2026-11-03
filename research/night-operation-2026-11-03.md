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

Status i identyfikator rzeczywistego przebiegu zostaną dopisane po uruchomieniu.
