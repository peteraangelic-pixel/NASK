# Porównanie programów hack.cert.pl

Źródło: NASK codex/multi-program-lab-20261103, research/porownanie-programow.md
(pełny plik, pierwszy z dwóch chunków)

Weryfikacja: 2026-11-03, Europe/Warsaw. Przeczytano karty wszystkich pięciu programów,
regulamin platformy, FAQ oraz pełne regulaminy PDF edycji 11/2026. Tabele i terminy na
stronach 3-4 każdego PDF sprawdzono także wizualnie. Warunki mogą być zmieniane przez
organizatora; przed rozpoczęciem kolejnego etapu należy sprawdzić aktualną wersję.

## Rekomendacja

**Pierwszy wybór: NASK. Drugi: CERT Polska.** Gov.pl jest sensowną alternatywą dla analizy
publicznego WWW. mSzyfr zostawiamy na etap, w którym mamy potwierdzoną możliwość
legalnego dostępu do funkcji aplikacji. Władysławowo ma niższe stawki, mniejszą pulę i
dłuższy termin rozstrzygnięcia.

To ocena atrakcyjności warunków, nie oszacowanie prawdopodobieństwa wygranej. Nie
sprawdzono jeszcze technologii, dostępności kont ani jakości zabezpieczeń systemów
NASK/CERT/COI/mSzyfr. Nie wiemy, ile zgłoszeń już wpłynęło ani ile puli pozostało.

## Pieniądze i terminy

Kwoty w PLN; kolejność stawek: niska / średnia / wysoka / krytyczna według CVSS 4.0.

| Program | Stawki główne | Drugi poziom | Początkowa pula edycji | Wyniki po końcu edycji | Nagrody w trakcie edycji |
| --- | --- | --- | --- | --- | --- |
| NASK | Tier 1: 600 / 4000 / 9000 / 20000 | Tier 2: 300 / 2000 / 4500 / 10000 | 100000 | do 30 dni | dopuszczone |
| CERT Polska | Tier 1: 600 / 4000 / 9000 / 20000 | Tier 2: 300 / 2000 / 4500 / 10000 | 100000 | do 30 dni | dopuszczone |
| Portal Gov.pl / COI | 600 / 4000 / 9000 / 20000 | brak podziału | 100000 | do 30 dni | dopuszczone |
| mSzyfr | 600 / 4000 / 9000 / 20000 | brak podziału | 100000 | do 30 dni | dopuszczone |
| Gmina Władysławowo | Tier 1: 200 / 1000 / 2000 / 4000 | Tier 2: 100 / 500 / 1000 / 2000 | 10000 | do 90 dni | brak analogicznego zapisu |

Wszystkie edycje przyjmują zgłoszenia od 3 do 30 listopada 2026. Wypłata: do 60 dni od
ogłoszenia wyników. Cztery większe programy dopuszczają wcześniejsze rozstrzygnięcia,
ale nie obiecują natychmiastowej wypłaty. Standardowy harmonogram może więc wynosić łącznie
30 + 60 dni po końcu edycji, a we Władysławowie 90 + 60 dni. Regulaminy zastrzegają
możliwość zmian terminów.

Same nagrody nie są gwarantowane przez znalezienie podejrzanego zachowania: zgłoszenie
musi zostać potwierdzone i zakwalifikowane przez komisję. Wszędzie liczy się pierwsze
prawidłowe zgłoszenie tej samej luki. Organizator rozlicza dodany składnik podatkowy;
zgodnie z FAQ podane stawki są kwotami przelewu dla zwycięzcy. Wygraną trzeba potwierdzić
na platformie w ciągu 7 dni.

**Szczegół NASK:** §7 pkt 9 liczy ten sam błąd źródłowy we wspólnym lub skopiowanym
kodzie, komponencie czy konfiguracji jako jedną podatność, nawet na wielu serwisach.
Nie zakładamy osobnych nagród za każdą kopię.

Suma początkowych pul tych pięciu regulaminów to 410000 zł. Wzmianka o milionie złotych
w artykule nie oznacza, że taki budżet jest dostępny w pojedynczej edycji lub programie.

## Zakres i praktyczna dostępność

### NASK

- Tier 1: `nask.pl`, `dyzurnet.pl`, `dns.pl`, `oad.nask.pl`, `zglos-dezinformacje.nask.pl`.
- Tier 2: `bezpiecznymiesiac.pl`, `secure.edu.pl`, `bezpiecznewybory.pl`, `116sos.pl`,
  `pllum.org.pl`, `science.nask.pl`, `dataannotation.pllum.org.pl`.
- To lista 12 hostów, bez wildcardu. Nie rozciągamy jej automatycznie na `www`, inne
  subdomeny, zaplecza dostawców ani adresy zewnętrznych integracji.
- Powód pierwszeństwa: kilka oddzielnych serwisów daje możliwość wyboru konkretnej
  funkcji do pogłębienia, przy wysokich stawkach Tier 1.

### CERT Polska

- Tier 1: `cert.pl`, `m.cert.pl`, `incydent.cert.pl`, `moje.cert.pl`, `n6portal.cert.pl`,
  `mwdb.cert.pl`, `hack.cert.pl`.
- Tier 2: `*.cert.pl`, `ctf.hack.cert.pl`.
- Wyłączenia w PDF: `*.hack.cert.pl`, `*.lab.cert.pl`. Karta WWW wyjaśnia wyjątek dla
  `ctf.hack.cert.pl`; PDF jednocześnie jawnie wymienia ten host i wyłącza pasujący
  wildcard. Przed testami tego hosta należy rozstrzygnąć tę niejednoznaczność. Do
  początkowego etapu go nie wybieramy.
- Karta programu mówi, że organizator nie udostępnia dedykowanych kont testowych.
- Ciekawy kierunek: kontrola uprawnień i izolacji własnych danych w aplikacjach, jeśli
  dostępne są odpowiednie funkcje i własne konta. Obecność `hack.cert.pl` w Tier 1
  potwierdzono. Nowa platforma nie jest dowodem słabszych zabezpieczeń.

### Portal Gov.pl / COI

- Wyłącznie `www.gov.pl`; nie cały wildcard `*.gov.pl` ani wszystkie systemy
  administracji.
- Stawki jak Tier 1 NASK, bez podziału na poziomy.
- Propozycja: publiczne funkcje wyszukiwania, prezentacji treści i pobierania załączników,
  o ile zostaną stwierdzone podczas przeglądu. Dostęp redakcyjny i współpraca
  pracowników nie są założeniami naszego planu.

### mSzyfr

- Zakres: `*.komunikator.narodowy.gov.pl`; karta oznacza program jako Web.
- Nie rozszerzamy automatycznie zakresu na aplikacje mobilne, inne domeny ani
  infrastrukturę rządową.
- Brak dedykowanych kont testowych według karty. Przed inwestowaniem czasu sprawdzamy
  możliwość uzyskania własnego zwykłego konta. Nie zakładamy możliwości zakładania kont
  służbowych ani przywilejów pracownika.
- Testy izolacji własnych rozmów i załączników mają sens dopiero po potwierdzeniu
  dostępu; łamanie kryptografii komunikatora nie jest pierwszym planem.

### Władysławowo

- Tier 1: `eobieg.wladyslawowo.pl`, `bip.wladyslawowo.pl`.
- Tier 2: `wladyslawowo.pl`, `cciod.wladyslawowo.pl`.
- Jedno zwykłe otwarcie HTTPS eObieg w używanej przeglądarce zakończyło się timeoutem;
  BIP zwrócił błąd połączenia. Nie wykonywano prób obejścia ograniczeń ani skanowania.
  Nie przesądza to o dostępności z komputera użytkownika lub innych sieci.

## Wspólne warunki wpływające na strategię

Zgodnie z regulaminami i kartami programów:

- Maksymalne tempo automatycznych narzędzi: 5 żądań/s. Projektowo proponujemy początkowo
  1 żądanie/s łącznie, z pojedynczym wspólnym ogranicznikiem; to nasz wybór, nie
  dodatkowy wymóg organizatora.
- Konta wyłącznie własne lub testowe, bez kont domenowych organizacji. Systemy dostępne
  przez VPN i szczególne uprawnienia pracowników są poza zakładanym etapem.
- Zakaz DoS, obciążeń, spamu i socjotechniki. Regulamin platformy zabrania przetwarzania,
  kopiowania i usuwania danych osobowych lub poufnych osób trzecich. Dowód powinien używać
  własnych syntetycznych danych i nie wymagać faktycznego przejęcia infrastruktury.
- Brak nagłówków, numery wersji, publiczne dane, self-XSS, czysto teoretyczne CVE i
  niepotwierdzone wyniki skanera nie są dobrym materiałem na nagrodę. Wyłączenia w czterech
  większych programach są zasadniczo wspólne.
- Zgłoszenie przez platformę; pełnoletność, PESEL i polska rezydencja podatkowa. Logowanie
  przez Login.gov.pl. Własną tożsamością i akceptacją warunków zarządza uczestnik.
- Poufność szczegółów podatności do jej usunięcia. Trzy kolejne niepotwierdzone lub
  niezgodne zgłoszenia mogą spowodować czasową blokadę zgłaszania, niezależnie od programu.
- Regulamin platformy przewiduje możliwość zawieszenia zgłoszeń i wypłat, m.in. z powodu
  wyczerpania puli lub możliwości weryfikacji. Kwoty w tabeli nie potwierdzają aktualnego
  salda.

## Pomysły i pierwszy etap pracy

Proponowany budżet pierwszego rekonesansu: 2 godziny. Najpierw NASK Tier 1, następnie
jeden wybrany serwis CERT Tier 1. Jeśli w 2 godziny nie pojawi się konkretna hipoteza
oparta na widocznej funkcji, zmieniamy funkcję lub program. Nie budujemy dużego skanera
przed takim rozpoznaniem.

1. Ustalić dostępne publiczne funkcje, konta, rzeczywiste hosty i przekierowania.
   Przekierowanie na niewymieniony host nie rozszerza upoważnienia do testów. Wynik: mała
   mapa funkcji oraz lista kwestii wymagających wyjaśnień.
