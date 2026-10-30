# Jurnalul agenților

Fiecare agent care lucrează în acest depozit adaugă la final o intrare scurtă, sub cea mai recentă. Nu modifica intrările altor agenți. Lecțiile care folosesc și altor proiecte le treci și în [memorie.md](memorie.md). Ce face fiecare agent chiar acum și evenimentele pe ore (început, rezervări, commit-uri) sunt în [agent-activity.md](agent-activity.md).

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
- Lecții: confirmi peretele și componentele înainte de randare. Cu tavanul măsurat ca scară, cotele estimate din fotografia calibrată au ieșit la mai puțin de 2 cm de cele măsurate; cu tavanul presupus (280 în loc de 270 cm), ieșeau cu ~4 % mai mari. Semnarea GPG nu merge din sesiunile agenților, așa că utilizatorul a acceptat commit-uri nesemnate.

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
- Rezultat: ghidul tiparului de design, trimis celorlalte cinci sesiuni ale depozitului și trecut în [memorie.md](memorie.md). Scripturile cuierului sunt acum în `.github/surse/cuier-hol/`, cu README, și regenerează identic imaginile publicate; PDF-ul diferă doar prin data creării. Commit-ul „Salvează sursele care generează imaginile cuierului”.
- Lecții: `sips` păstrează coordonatele GPS la conversie; fotografiile se salvează doar cu PIL.

### 2026-10-29 · Depozit · agentul Designer interior și memoria comună
- Cerere: un agent al depozitului pentru toate amenajările casei, care învață de la ceilalți agenți, ține memoria depozitului și scrie totul în română. Apoi un `agent-activity.md`, cu activitatea agenților.
- Rezultat: agentul `.github/agents/designer-interior.agent.md`, memoria comună din `.github/memorie/` și regulile pentru toți agenții din `.github/copilot-instructions.md`. Memoria a pornit de la toate sesiunile de până acum, iar regulile principale sunt salvate și în Copilot Memory. [agent-activity.md](agent-activity.md) arată cine lucrează acum, la ce și în ce fișiere, plus evenimentele pe ore, de la prima sesiune încoace; rezervările fișierelor comune se fac acum acolo. Commit-urile „Adaugă agentul Designer interior și memoria comună a agenților” și „Adaugă agent-activity.md cu activitatea agenților”.
- Lecții: amintirile Copilot ale depozitului vechi nu au trecut la cel nou, de aceea memoria completă stă în fișiere. Un mesaj trimis unei sesiuni inactive o pornește din nou, așa că rezervările stau în `agent-activity.md`, iar mesajele merg doar la agenții care lucrează chiar acum.

### 2026-10-29 · Polițe viniluri · peretele cu televizorul
- Cerere: polițe integrate pe peretele cu televizorul (419 × 250 cm), pentru viniluri, din stejar asortat cu comoda Cioata Veneto 242. Televizor TCL 98C8L de 98", boxe Klipsch RP-504C II și RP-8000F II. Totul într-un folder separat.
- Rezultat: proiectul [Polite viniluri](../../Polite%20viniluri/README.md). După corecturi: două polițe flotante din stejar, de 80 × 33 × 4 cm, doar în dreapta televizorului, deasupra boxei de podea, la 10 cm de televizor și la 10 cm de capătul peretelui. Sunt prinse direct în perete, pe câte 4 tije M12 ascunse în lemn (13 cm în ancoră chimică, 25 cm în poliță), fără console sau suporți la vedere. Discurile stau în picioare, între opritoare, iar cele de sus se termină la nivelul marginii de sus a televizorului; încap ~268 de discuri. Propunerea A are opritoarele îmbrăcate în stejar, iar varianta B, opritoare din oțel negru mat. Livrabile: randări A și B, comparație, plan A3 la 1:15, cu detaliile la 1:3 și 1:5 și lista cotelor de măsurat, listă de materiale (prinderea de la Dedeman, 156,45 lei; opritoarele de pe eMAG, 60 lei; polițele la comandă, de la Cioata sau de la tâmplar), montaj pas cu pas. Sursele sunt în `.github/surse/polite-viniluri/` și regenerează identic imaginile. Commit-ul „Adaugă proiectul polițelor pentru viniluri de pe peretele cu televizorul”.
- Corecturi:
  - prima propunere, cu două corpuri închise de 80 × 79 × 38 cm cu câte 4 compartimente, a fost respinsă: „nu doresc să arate ca niște cutii”, „mai moderne și mai minimaliste”;
  - a doua, cu 4 polițe flotante de 6 cm, câte două de fiecare parte a televizorului și cu varianta B pe console L negre, a fost corectată: fără console („polițele direct prinse în perete, fără ca prinderile să fie vizibile”, „să nu aibă suporții negri”), polițe doar în dreapta televizorului și „puțin mai subțiri”.

  Versiunile vechi au rămas doar în istoricul sesiunii, nu în depozit.
- Întrebări fără răspuns: din ce e peretele și cât e de gros, codul de finisaj al comodei, înălțimea camerei (poza dă ~262 cm, nu 250), dacă trecerea din dreapta are ușă, pe unde trec cablurile sub dispozitivul alb.
- Lecții: în [memorie.md](memorie.md), la „Polițe viniluri”: calibrarea pe obiecte cunoscute, curățarea ecranelor și a persoanelor din poze, dimensiunile pentru viniluri, polițe flotante în loc de corpuri, planul la 1:15 pentru un perete de 4 m, fără console și cu tijele verificate în cazul cel mai rău, ambiguitatea cuvântului „suport”, copertele care nu trebuie să semene cu stejarul, bufferul de adâncime, verificarea prețurilor și Cioata la comandă.

### 2026-10-30 · Depozit · uneltele agenților
- Cerere: să fie salvat ce fac acum agenții în depozit, adică uneltele și felul în care lucrează, ca să poată fi folosite și pe viitor.
- Rezultat: uneltele comune din [.github/unelte/](../unelte/README.md), pe ramura `unelte-agenti`, cu pull request; site-ul nu se schimbă până la unirea în `master`.
  - 10 module Python: fotografia fără metadate, segmentele și calibrarea camerei, randarea, materialele, comparația, planul A3 cu verificarea textelor, rezistența, prețurile și verificarea unui proiect înainte de commit. Sunt preluate din sursele cuierului, ale polițelor și ale proiectului cu beton.
  - 56 de teste, fără rețea. Ele verifică și că uneltele dau aceleași rezultate ca scripturile proiectelor, de exemplu aceeași calibrare: rms 0,5956 px la polițe și 0,5961 px la cuier.
  - README-ul are catalogul, pașii unui proiect nou cu comenzile lor, uneltele lui Copilot, lucrul cu subagenți și capcanele. Exemplele din el au fost rulate pe fotografia polițelor, iar `preturi.py`, pe un server local.
  - Agentul Designer interior, `copilot-instructions.md` și memoria trimit acum la unelte. `.gitignore`-ul din rădăcină ignoră `.venv/`, `out/` și `__pycache__/`.
  - Scripturile proiectelor publicate au rămas neschimbate.
  - Commit-ul „Adaugă uneltele comune ale agenților în .github/unelte”.
- Cum s-a lucrat: s-au citit sursele celor trei proiecte, inclusiv ramura cu beton, memoria, jurnalul și istoricul git. Funcțiile comune au intrat în module cu nume în română, iar testele de paritate rulează fiecare unealtă alături de scriptul din care vine.
- Corecturi: niciuna de la utilizator. Rularea exemplelor din README a arătat că primele exemple de calibrare erau greșite: cu 4 grupuri de muchii, poziția televizorului fugea la 803 cm, iar cu muchii doar din planul peretelui, distanța focală ajungea la 7 px. Exemplul are acum 12 grupuri, cu muchiile comodei.
- Lecții: în [memorie.md](memorie.md), la „2026-10-30 · Depozit”: scripturile copiate între proiecte duceau greșelile mai departe, iar o calibrare cu eroare mică poate fi totuși greșită. Celelalte capcane sunt în README-ul uneltelor: `scaled(k)` e relativ la fotografie, harta de lumină are un singur canal, Pillow copiază comentariul JPEG, iar randarea cere k1 = 0 (`fara_distorsiune()`).
