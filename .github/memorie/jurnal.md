# Jurnalul agenților

Fiecare agent care lucrează în acest depozit adaugă la final o intrare scurtă, sub cea mai recentă. Nu modifica intrările altor agenți. Lecțiile care folosesc și altor proiecte le treci și în [memorie.md](memorie.md).

Formatul unei intrări:

```text
### AAAA-LL-ZZ · <proiect> · <ce s-a cerut, pe scurt>
- Cerere: ce a cerut utilizatorul.
- Rezultat: ce s-a livrat și commit-ul, dacă există.
- Corecturi: ce a corectat utilizatorul.
- Lecții: ce trebuie să știe agentul următor.
```

## Intrări

### 2026-10-29 · Cuier hol · propunerea de cuier
- Cerere: un cuier lângă fereastra din hol, pornind de la o fotografie. Apoi lista de cumpărături cu prețuri și linkuri, depozitul pe GitHub, în română, și montajul pas cu pas, foarte detaliat.
- Rezultat: panou riflaj din stejar pe pâslă neagră, cu 5 cârlige negre mat (3 la 178 cm și 2 la 150 cm); varianta B negru sau antracit; randări pe fotografie, comparație, plan tehnic A3 la 1:15 și listă de materiale de ~440 lei. Commit-urile „Adaugă proiectul cuierului din hol” și „Adaugă montajul pas cu pas pentru cuierul din hol”.
- Corecturi: cuierul se mută în stânga ferestrei și nu are bancă.
- Lecții: confirmi peretele și componentele înainte de randare. Cotele estimate din fotografia calibrată au ieșit la mai puțin de 2 cm de cele măsurate. Semnarea GPG nu merge din sesiunile agenților, așa că utilizatorul a acceptat commit-uri nesemnate.

### 2026-10-29 · Cuier hol · plinta
- Cerere: plinta are 80 × 16 mm, iar panoul nu trebuie să coboare sub muchia ei de sus. Coordonare cu agentul cuierului.
- Rezultat: panoul de 44 × 223,5 cm stă pe plintă, de la 8 la 231,5 cm, iar plinta rămâne întreagă. Randările, comparația și planul au fost regenerate, cu detaliul A la 1:3. Commit-ul „Așază panoul cuierului pe plintă”.
- Lecții: protocolul de coordonare a funcționat: exclusivitate pe fișiere până la „Am terminat”, un singur agent face commit-ul și nimeni nu răspunde la confirmări cu alte confirmări. În randare, plinta se așază unde apare în fotografie (~7,3 cm), nu la cota măsurată.

### 2026-10-29 · Depozit · curățarea documentației
- Cerere: README-ul din rădăcină cu detalii generale și legături către README-ul fiecărui folder, plus un README propriu în fiecare folder.
- Rezultat: commit-ul „Reorganizează documentația pe proiecte”.

### 2026-10-29 · Site · publicarea documentației
- Cerere: un site static pe GitHub, în română, ca documentația să poată fi trimisă altora. Apoi redenumirea și anonimizarea depozitului, ca să poată deveni public.
- Rezultat: site GitHub Pages generat cu Jekyll din fișierele Markdown, publicat la fiecare push pe `master`. Depozitul public `design-interior`, cu istoricul rescris fără adresă și cu emailul noreply. Commit-urile „Adaugă site-ul GitHub Pages pentru documentație” și „Pregătește depozitul pentru publicare”.
- Lecții: orice folder cu `README.md` apare singur în meniul site-ului, iar `.github/` nu se publică. Imaginile se verifică pentru EXIF și pentru numere de înmatriculare.

### 2026-10-29 · Peretele cu televizorul · polițe pentru viniluri (în lucru)
- Cerere: amenajarea peretelui cu televizorul, de 419 × 250 cm, cu polițe integrate pentru viniluri, din stejar, asortate cu comoda. Televizor TCL 98C8L, comodă Cioată Veneto de 242 × 67 cm, boxe Klipsch RP-504C II și RP-8000F II. Proiectul are folderul lui.
- Rezultat: în lucru. Agentul a primit tiparul de design de la agentul cuierului.

### 2026-10-29 · Cuier hol · tiparul de design și scripturile
- Cerere: sincronizarea cu ceilalți agenți, ca toți să urmeze același tipar de design.
- Rezultat: ghidul tiparului de design, trecut în [memorie.md](memorie.md). Scripturile cuierului sunt acum în `.github/surse/cuier-hol/`, cu README, și regenerează identic imaginile publicate.
- Lecții: `sips` păstrează coordonatele GPS la conversie; fotografiile se salvează doar cu PIL.

### 2026-10-29 · Depozit · agentul Designer interior și memoria comună
- Cerere: un agent al depozitului pentru toate amenajările casei, care învață de la ceilalți agenți, ține memoria depozitului și scrie totul în română.
- Rezultat: agentul `.github/agents/designer-interior.agent.md`, memoria comună din `.github/memorie/` și regulile pentru toți agenții din `.github/copilot-instructions.md`. Memoria a pornit de la toate sesiunile de până acum, iar regulile principale sunt salvate și în Copilot Memory.
- Lecții: amintirile Copilot ale depozitului vechi nu au trecut la cel nou, de aceea memoria completă stă în fișiere.
