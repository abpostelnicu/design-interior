# Memoria comună a agenților

Aici agenții care lucrează în acest depozit păstrează ce au învățat, ca agentul următor să nu pornească de la zero. Orice agent citește acest fișier înainte de un proiect de amenajare și îl actualizează la final. Ce a făcut fiecare sesiune, pe scurt, e în [jurnal.md](jurnal.md), iar cine lucrează acum, la ce și în ce fișiere, în [agent-activity.md](agent-activity.md). Proiectele noi le face agentul [Designer interior](../agents/designer-interior.agent.md).

Reguli pentru acest fișier:
- Scrie în română, scurt, ca fapte verificabile. La lecții notezi data și proiectul.
- Fără date personale: adresa casei, numere de înmatriculare, nume, coordonate GPS sau căi absolute de pe calculator.
- Când o informație se schimbă, de exemplu o cotă remăsurată, o corectezi pe loc. Nu lași două valori contradictorii; istoricul rămâne în jurnal.
- Aici intră doar ce folosește și altor proiecte. Detaliile unui singur proiect stau în README-ul lui.
- Fă editări mici și punctuale: alți agenți pot scrie în același timp în acest fișier.

## Preferințele utilizatorului

- **Limba:** totul în română: documente, note de pe planuri, mesaje de commit, răspunsuri și mesaje între agenți. Numele de fișiere sunt fără diacritice.
- **Un folder pentru fiecare amenajare**, cu README propriu. README-ul din rădăcină are doar o prezentare generală și un tabel cu legături către README-ul fiecărui folder și ce conține acesta.
- **Propunere vizuală pe fotografia lui**, în două variante, plus comparația cu situația actuală.
- **Variantele noi se adaugă, nu înlocuiesc:** o propunere nouă pentru același loc intră în `master` ca variantă în plus, în folderul proiectului existent, nu într-unul nou. Primește literele următoare (după A și B vin C și D), fișiere cu nume noi și o secțiune nouă la finalul README-ului, iar fișierele existente rămân neschimbate („Adu în master ca varianta la variantele deja existente, nu suprascrie ce este acum în master”, „totul ar trebui băgat în același folder în care sunt și polițele din stejar”). Sursele ei stau într-un subfolder al surselor proiectului, `.github/surse/<proiect>/<varianta>/`. La fel la aducerea în `master` a muncii de pe ramuri: planurile și imaginile existente nu se suprascriu.
- **Proiecte executabile cu materiale din comerț**, cu prețuri estimative și linkuri. Pentru piesele făcute la comandă vrea și căile de procurare („inclusiv prețuri și moduri de procurare”): cine le face, cu linkuri, prețuri de referință și un mesaj gata de trimis pentru cererea de ofertă.
- **Montaj pas cu pas foarte detaliat.**
- **Fără elemente adăugate din proprie inițiativă.** A respins banca de la cuier. Extra-urile apar doar ca opțiuni în text.
- **Stil și materiale:** stejar natur și negru mat. Tâmplăria și ușa de intrare sunt negre sau antracit. Polițele de pe peretele cu televizorul trebuie să fie din stejar, asortate cu finisajul comodei. Ca variantă în plus, a cerut și polițe din beton decorativ, în stilul modern care îmbină lemnul natural cu betonul, cu polițele orizontale legate de verticale.
- **Modern și minimalist, nu cutii:** a respins corpurile închise tip cutie pentru viniluri („nu doresc să arate ca niște cutii”, „mai moderne și mai minimaliste”), apoi și consolele la vedere („polițele doresc să fie direct prinse în perete, fără ca prinderile să fie vizibile”, „să nu aibă suporții negri”). Preferă polițe flotante, subțiri, prinse ascuns direct în perete, și cât mai puține elemente la vedere.
- **Cote:** le dă ca listă numerotată, uneori doar cifre în mm. Scrie-i cum le-ai interpretat.
- **Commit și push:** de obicei le cere explicit, la final. Fiecare push pe `master` republică site-ul public.
- **Agenți în paralel:** lucrează des cu mai mulți agenți deodată și vrea ca ei să se coordoneze și să urmeze același tipar de design. Vrea să vadă într-un singur loc ce face fiecare agent: [agent-activity.md](agent-activity.md).
- **Memorie:** vrea ca tot ce se lucrează să rămână salvat pentru agenții următori: în acest fișier, în jurnal și în Copilot Memory.

## Casa: cote și date pe încăperi

Aici trec doar cotele măsurate și datele primite de la utilizator. Ce e estimat din poză are „~” în față.

### Holul de la intrare

- Tavanul: 270 cm.
- Peretele dintre colț și golul ferestrei, în stânga ferestrei: 55 cm.
- Partea de sus a golului ferestrei: 231,5 cm de la pardoseală. Utilizatorul a scris „385 mm”, interpretat ca distanța dintre golul ferestrei și tavan; poza dă tot ~231–233 cm.
- Plinta: 8 cm înălțime și 1,6 cm grosime. Nu se taie.
- Pereții: cărămidă.
- Ușa de intrare se deschide la 90° spre peretele cu fereastra. Deschisă, ajunge la ~34 cm de perete.
- Tâmplăria și ușa de intrare: negre sau antracit.
- Peretele din dreapta ferestrei, estimat din poză: ~65 cm liberi între golul ferestrei și colț. Pe el sunt, cu marginea de jos și distanța de la colț până la centrul plăcii: senzorul ~2,03 m și ~22 cm, întrerupătorul ~0,86 m și ~15 cm, priza ~0,24 m și ~32 cm. Termostatul e chiar în colț, cu marginea de jos la ~1,28 m. Golul ușii din dreapta începe pe peretele lateral, la ~12 cm de colț, iar capul ei e la ~1,92 m.
- Proiect: „Cuier hol”.

### Peretele cu televizorul

- Peretele: 419 cm lățime; înălțimea dată de utilizator e 250 cm, dar fotografia calibrată pe televizor și comodă dă ~262 cm (cu 250, eroarea calibrării crește de la 0,6 la 4,6 px). De remăsurat.
- Televizorul: TCL 98C8L, 98", 216,6 × 123,6 × 5,4 cm, 57,5 kg, VESA 600 × 500. Din poză: de la ~83 la ~206,6 cm, cu axul la ~210,7 cm de colțul din stânga (practic la mijlocul peretelui).
- Comoda TV: Cioată Veneto, 242 × 48 × 67 cm, pe picioare de 14 cm ([pagina produsului](https://www.cioata.eu/comoda-tv-veneto-242cm.html)): stejar masiv, fronturi din microciment antracit. Din poză: de la ~84,8 la ~326,8 cm de colț, la ~8,7 cm de perete. Finisajul (CS, NO, FE sau SO) nu e confirmat; în poză seamănă cu Natural Oak.
- Boxele: centru Klipsch RP-504C II (81,4 × 17,4 × 38,3 cm), pe comodă; de podea Klipsch RP-8000F II (27,5 × 109,5 × 46,3 cm cu picioare, port de bas în spate), din poză la ~14–43 și ~388–415 cm de colț, la ~8 cm de perete.
- Sus, în dreapta televizorului, e un dispozitiv alb, de la ~222,7 la ~248,5 cm înălțime, la ~348,5–373,7 cm de colț. Nu se acoperă.
- Plinta: ~7,5 cm, din poză. Peretele: presupus din cărămidă, neconfirmat.
- Proiect: „Polite viniluri”: 2 polițe flotante din stejar, de 80 × 33 × 4 cm, doar în dreapta televizorului (cerut de utilizator), de la ~329 la ~409 cm de colț, prinse pe tije ascunse. Peretele se termină la 419 cm într-o trecere; nu se știe dacă are ușă.
- Proiect: „Polite viniluri”, variantele C și D, în același folder cu A și B, cu fișiere noi: aceleași 2 polițe, din microciment pe miez de placaj, legate de o verticală din stejar masiv de 4 cm. Lucrate pe ramura `polite-viniluri-beton` și aduse în `master` prin [pull request-ul #1](https://github.com/abpostelnicu/design-interior/pull/1). Verticala e lipită de polița de jos și are fața din stânga la ~387,6 cm de colț, în dreptul marginii din stânga a boxei de podea.

## Tiparul de design

Tiparul a fost stabilit la proiectul „Cuier hol”, care rămâne referința ([pagina de pe site](https://abpostelnicu.github.io/design-interior/Cuier%20hol/)). Fiecare proiect nou trebuie să arate și să fie documentat la fel. Uneltele cu care lucrezi, comenzile fiecărui pas și testele sunt în [.github/unelte/](../unelte/README.md). Scripturile cuierului, din [.github/surse/cuier-hol/](../surse/cuier-hol/README.md), rămân exemplul complet al unui proiect.

### Ce livrezi pentru fiecare proiect

Fiecare proiect are un folder propriu la rădăcina depozitului, cu nume scurt în română, de exemplu `Cuier hol`. Numele poate avea spații, dar nu conține date personale.

| Fișier | Ce conține |
|---|---|
| `README.md` | Pagina proiectului; structura e descrisă mai jos |
| `comparatie_acum_vs_propuneri.jpg` | Trei imagini alăturate: „Acum”, „Propunere A – <material>” și „Varianta B – <material>”. Fiecare are un titlu bold și un subtitlu gri, cu dimensiunile principale. |
| `propunere_A_<material>.jpg` | Varianta A, randată în fotografia originală, cu aceeași încadrare, la de două ori rezoluția fotografiei |
| `varianta_B_<material>.jpg` | Varianta B, randată la fel |
| `plan_tehnic_<proiect>.pdf` și `.png` | Planul tehnic, pe A3 orizontal, la scara 1:15 |
| `lista_materiale.md` | Lista de cumpărături, cu prețuri verificate și linkuri |

**Variantele:** A e varianta naturală, de exemplu stejar. B e varianta închisă la culoare, negru sau antracit, asortată cu tâmplăria și ușile.

**Structura `README.md`:**
- titlul;
- linkul `[Înapoi la prezentarea generală](../README.md)`;
- o descriere de 2–3 fraze: ce e, unde e, dimensiunile principale și variantele;
- imaginea de comparație;
- „Conținutul folderului”: tabel cu fișierele;
- „Cote măsurate”;
- „Montaj pas cu pas”, cu subsecțiunile:
  - „Cote de montaj”, un tabel Ce | Cât;
  - „Materiale și unelte”;
  - pașii numerotați `### 1. …`, `### 2. …`;
  - verificarea finală;
- „Întreținere”.

**Planul tehnic** are aceste vederi:
- vedere frontală;
- secțiune laterală;
- plan, adică vederea de sus, cu deschiderea ușilor;
- detalii la 1:3 unde e nevoie, de exemplu panoul pe plintă.

Pe plan sunt trei blocuri de note: MATERIALE ȘI FERONERIE, DE CE AȘA și COTE. Subtitlul planului conține dimensiunile, „cote în cm · scara 1:15 (A3)” și dacă cotele sunt măsurate sau estimate.

**Lista de materiale:**
- un coș principal dintr-un singur magazin, dacă se poate: Produs | Cant. | Preț | Subtotal | Link, plus totalul;
- alternative de la alte magazine;
- varianta B;
- alte opțiuni de feronerie;
- data verificării prețurilor, cu mențiunea că nu includ transportul.

**Indexul din rădăcină:** adaugi un rând pentru proiect în tabelul din `README.md`-ul de la rădăcină. Site-ul generează singur o pagină pentru orice folder care are `README.md`.

### Pașii de lucru, în ordine

1. **Fotografia.** O pregătești cu `foto.py pregateste`: 1024 px pe latura mare, în sRGB și fără metadate (vezi „Depozitul și site-ul”). Faci zoom-uri cu grilă de coordonate pe zona de lucru (`foto.py grila`) și notezi tot ce contează:
   - prize, întrerupătoare, senzori, termostat;
   - balamalele și sensul de deschidere al ușilor;
   - plinte, glafuri, rame.
2. **Calibrarea camerei** (`segmente.py` și `camera.calibreaza`). Din muchiile drepte ale camerei obții un model al aparatului foto. Cu el estimezi cote reale direct din poză: lățimi de perete, înălțimi, poziția prizelor. Scara vine din tavanul măsurat, pe care îl ceri primul, sau din obiecte cu dimensiuni din fișă, ca televizorul și comoda, cu tavanul lăsat necunoscut. Un tavan presupus îl folosești doar provizoriu, cu cotele marcate „~”. Îți trebuie și muchii care ies din perete, iar la final verifici că distanța focală și poziția aparatului au sens, nu doar eroarea RMS (pasul 3 din [README-ul uneltelor](../unelte/README.md)).
3. **Constrângerile.**
   - Ușile: în ce parte se deschid și cât loc rămâne la 90°, inclusiv mânerul.
   - Prizele și întrerupătoarele: le eviți sau faci decupaje.
   - Senzorii și termostatul nu se acoperă.
   - Plinta nu se taie.
   - Aliniamentele cu liniile existente: partea de sus a golului ferestrei, capul ușii, glaful.
4. **Designul.** Faci exact ce s-a cerut. Elementele în plus, cum ar fi o bancă sau o bandă LED, apar doar ca opțiuni în text, nu în randare.
5. **Randările** (`render.py` al proiectului, cu `randare.py` și `materiale.py`) și **comparația** (`comparatie.py`). Verifici rezultatul cu crop-uri mărite pe margini, pe contactul cu plinta sau pardoseala și pe feronerie.
6. **Planul tehnic** (`drawing.py` al proiectului, cu `plan.py`). După fiecare schimbare rulezi `plan.py verifica`, care găsește textele suprapuse, ieșite din pagină sau intrate în desene. Apoi te uiți pe crop-uri din PNG-ul la 220 dpi și verifici cu `plan.py a3` că PDF-ul e A3: `/MediaBox [ 0 0 1190.55 841.89 ]`.
7. **Cotele reale.**
   - Le ceri cu `ask_user`, ca listă concretă: a), b), c)…
   - Dacă utilizatorul nu răspunde, continui cu estimările marcate „~”.
   - Lista „cote de măsurat” o pui în PDF.
8. **Când primești cotele:**
   - le treci în `design.py`; în `SITE`, valorile estimate sunt marcate cu comentariul `# est.`;
   - recalibrezi camera cu tavanul măsurat;
   - regenerezi randările, comparația și planul.
9. **Lista de materiale.**
   - Cauți în magazine din România: Dedeman, eMAG, Hornbach, IKEA și magazine specializate.
   - Pui doar linkuri pe care le-ai deschis efectiv; nu inventezi niciodată URL-uri sau prețuri.
   - Prețul și ambalajul le citești cu `preturi.py`, iar `preturi.py --lista` reverifică toată lista de materiale.
   - Dedeman afișează prețul fără localitate, dar stocul abia după ce alegi localitatea.
   - Leroy Merlin blochează descărcarea automată a paginilor (403).
   - Paginile pe care `preturi.py` nu le poate citi (blocat, captcha, preț încărcat din JavaScript) le deschizi în browserul integrat: `openBrowserPage`, `navigatePage`, apoi `runPlaywrightCode` cu `page.locator('body').innerText()` și un filtru pe cuvinte, pentru că instantaneul întreg al paginii are sute de KB.
   - Pentru piesele făcute la comandă scrii și căile de procurare, în ordinea în care merită încercate: producătorul mobilierului asortat, un atelier, un tâmplar cu un set de materiale. Pui firme verificate pe site-ul lor, prețuri de referință și o cerere de ofertă gata de trimis, ca la variantele C și D din „Polite viniluri”.
   - Verifici că feroneria se potrivește peretelui. La cărămidă: dibluri Fischer DuoPower Ø6 și șuruburi destul de lungi ca să treacă prin panou până în perete.
10. **Montajul pas cu pas**, în `README.md`-ul proiectului.
    - Îl scrii pentru cineva care face singur montajul.
    - Conține ordinea operațiilor, cotele de montaj, uneltele, adâncimile de găurit (cu bandă pe burghiu), timpii adezivului, cum se taie fără să se ciupească furnirul și verificările finale.
11. **Verificările, commit-ul și push-ul**, ca mai jos. Verificările automate le rulezi cu `python -B .github/unelte/verificari.py "<Proiect>"`, care trebuie să dea 0 probleme.

### Scripturile

Uneltele comune sunt în [.github/unelte/](../unelte/README.md), cu catalogul, comenzile fiecărui pas, testele și capcanele. Pentru un proiect nou nu mai copiezi scripturile altui proiect. În `.github/surse/<proiect>/`, cu numele fără diacritice și cu cratimă între cuvinte, scrii doar ce e al proiectului: `design.py`, dreptele pentru calibrare, scena randată și planul. Ele importă uneltele cu `from unelte import …`. Scripturile cuierului, din [.github/surse/cuier-hol/](../surse/cuier-hol/README.md), și ale polițelor reproduc imaginile publicate și rămân exemple; nu modifici scripturile altui proiect. O unealtă nouă, folositoare și altor proiecte, o muți în `.github/unelte/`, cu test.

Mediul Python: `python3 -m venv .venv && .venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy`, din rădăcina depozitului. Python-ul sistemului nu are numpy. Scripturile le rulezi cu `python -B`, ca să nu apară `__pycache__`. Rezultatele se generează în `out/`, apoi se copiază în folderul proiectului cu numele finale. `.gitignore`-ul din rădăcină ignoră `.venv/`, `out/` și `__pycache__/` în tot depozitul.

Scripturile cuierului, pe care le-au urmat proiectele de până acum, au în `.github/unelte/` aceste corespondente: `camera.py` → `segmente.py` și `camera.py`, `render.py` → `randare.py` și `materiale.py`, `drawing.py` → `plan.py`, `compare.py` → `comparatie.py`. `design.py` rămâne al fiecărui proiect.

| Script | Ce face | Ce schimbi pentru o fotografie nouă |
|---|---|---|
| `camera.py` | Calibrează o cameră pinhole din segmentele de dreaptă grupate în `segments.json`. Necunoscute: distanța focală, distorsiunea k1, orientarea (yaw, pitch, roll), poziția și dimensiunile camerei. Salvează `camera_H<tavan>.json`. `Camera.backproject(uv, "Z", 0)` dă coordonatele reale ale unui pixel de pe perete. Rezultat bun: eroare RMS sub 1 px (la cuier, 0,6 px). | Detectezi segmentele cu `cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV)` și le alegi pe indici, în grupuri cu nume. Rescrii `_line3d` pentru camera ta: colțuri, tavan, pardoseală, ferestre, uși. Coordonate: X de-a lungul peretelui din spate, Y în sus, Z spre cameră, cu Z = 0 pe perete. |
| `design.py` | Sursa unică pentru cote. `SITE` conține cotele măsurate, iar cele estimate sunt marcate `# est.`. `D` conține parametrii designului. `Layout` așază obiectul față de pereți, fereastră și plintă. | Totul. |
| `render.py` | Randează în fotografie. `Canvas.face` aplică o textură pe un dreptunghi 3D prin omografie, `Canvas.multiply` aplică umbre și ocluzie, `cylinder` și `shade_metal` desenează piesele metalice. Textura de stejar e luată din pardoseala din poză, iar `wall_light_map` reproduce lumina de pe perete. Imaginea se calculează la de 4 ori rezoluția fotografiei și se micșorează la de 2 ori. `finish` adaugă un blur și zgomot fin, ca obiectul să se integreze în poză. | Elementele desenate și variantele (`VARIANTS`). În randare așezi obiectele după geometria din poză (`cam1.q`), ca să se alinieze vizual: la cuier, plinta apare în poză la 7,26 cm, deși măsurată are 8 cm. Planul tehnic folosește cotele măsurate. |
| `drawing.py` | Planul A3 la 1:15 (`MM = 10/15` mm de hârtie pe cm). Funcții ajutătoare: `make_axes`, `rect`, `hatch`, `dim_h`, `dim_v` (parametrul `k` pentru alte scări), `label`, `fmt` (virgulă zecimală). Fontul DejaVu Sans are diacritice. Scoate PDF și PNG la 220 dpi. | Vederile, notele și numele fișierului de ieșire. |
| `compare.py` | Imaginea cu trei panouri: Acum, A și B. Subtitlul se ia din `design.py`. | Titlurile și subtitlurile. |

### Limba și forma

- **Limba:** totul în română, inclusiv documentele, notele de pe planuri și mesajele de commit.
- **Diacritice:** în text da, cu ș și ț cu virgulă; în numele de fișiere nu (de exemplu `propunere_A_stejar.jpg`).
- **Cifre și unități:**
  - virgulă zecimală (231,5) și „×” între dimensiuni (44 × 223,5 cm);
  - cm pe planuri, mm pentru grosimi și feronerie;
  - „~” pentru valorile estimate; prețuri în „lei”.
- **Stil:**
  - texte scurte, la persoana a II-a („măsori”, „taie”, „verifică”);
  - liste și tabele în loc de paragrafe lungi;
  - fiecare termen tehnic explicat o dată.

### Depozitul și site-ul

- **Depozitul e public.** Nu conține date personale: adresa casei, numere de înmatriculare (atenție la mașinile din fereastră) sau coordonate GPS în fotografii.
  - Fotografia de pe telefon nu intră în depozit. Pozele de pe telefon au de obicei coordonate GPS, iar `sips` le păstrează la conversie (verificat).
  - În depozit pui doar imagini generate sau salvate din nou cu OpenCV sau PIL, care nu păstrează metadatele EXIF. Fotografia de lucru din `.github/surse/<proiect>/original.jpg` o pregătești cu `foto.py pregateste` din `.github/unelte/`: o rotește după EXIF, o trece în sRGB și o salvează fără EXIF, GPS, XMP sau comentariu JPEG. `foto.py exif` verifică o imagine înainte de commit.
- **Căile absolute** de pe calculator nu apar în fișiere: numele folderului local conține date personale.
- **Adresa de email:** commit-urile se fac cu adresa „noreply” de la GitHub, care e deja setată local în depozit. Verifici cu `git config user.email`. Asta e valabil pe calculatorul utilizatorului. Identitatea folosită efectiv o verifici, oriunde, cu `git var GIT_AUTHOR_IDENT`. Comanda ține cont și de variabilele de mediu `GIT_AUTHOR_*` și `GIT_COMMITTER_*`, care au prioritate față de `git config` și de `-c user.…`. În clona din cloud, variabilele erau deja setate, cu numele de utilizator de pe GitHub și adresa „noreply”. Dacă într-o clonă nouă numele și adresa lipsesc, le iei din `git log` și le pui doar pe comandă, cu `git -c user.name=… -c user.email=… commit …`.
- **Mesajele de commit:** în română, la imperativ, de exemplu „Adaugă…” sau „Așază…”. La final pui rândul `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
- **Semnătura GPG.** Configurația globală cere commit-uri semnate, dar parola se introduce într-o fereastră pinentry pe care un agent nu o poate completa. Utilizatorul a aprobat commit-uri nesemnate pentru acest depozit, așa că folosești `git -c commit.gpgsign=false commit …`. Opțiunea se pune doar pe comandă; configurația nu se modifică.
- **Fără arhive:** în depozit nu se păstrează variante vechi; utilizatorul a cerut ștergerea arhivei. `.DS_Store` e ignorat.
- **Site-ul:** <https://abpostelnicu.github.io/design-interior/> se publică automat la fiecare push pe `master`. Push-ul altor ramuri nu-l republică: `.github/workflows/publicare-site.yml` pornește doar la `master` sau manual.
  - Linkurile rămân relative; spațiile din numele folderelor se scriu `%20`.
  - Orice folder cu `README.md` apare singur în meniul site-ului. Folderele care încep cu punct, ca `.github/`, nu se publică.
  - Imaginea afișată când se trimite linkul este `imagine_implicita` din `_config.yml`.

### Coordonarea între agenți

- **Activitatea:** cine lucrează acum, la ce și în ce fișiere e în [agent-activity.md](agent-activity.md). Când începi să modifici fișiere, te treci acolo, îți ții rândul la zi și îl scoți la final. Regulile sunt în fișier.
- **Foldere proprii:** fiecare agent lucrează în folderul proiectului său. Un proiect aparține sesiunii care l-a început, până când utilizatorul spune altfel; sesiunea fiecărui proiect e în tabelul „Proiecte”, mai jos.
- **Fișiere comune:** `README.md` din rădăcină, `_config.yml`, `_layouts/`, `assets/` și `.github/`, inclusiv această memorie.
  - Înainte să le modifici, verifici în `agent-activity.md` că nu le-a rezervat alt agent, apoi le rezervi tu acolo, în rândul tău.
  - Agenților care lucrează chiar acum și ar putea atinge aceleași fișiere le scrii și cu `send_message`, ca să ceri exclusivitate: „până îți confirm că am terminat, modific doar eu X”. Sesiunile inactive nu le trezești cu mesaje: un mesaj pornește din nou sesiunea, iar rezervarea o văd oricum în fișier.
  - Cel care primește anunțul sau vede rezervarea nu editează acele fișiere, nu rulează scripturile care le regenerează și nu face commit până nu sunt eliberate.
  - Când termini, eliberezi rezervarea în `agent-activity.md`. Dacă ai anunțat pe cineva, îi trimiți „Am terminat” și spui pe scurt ce ai schimbat. Celălalt verifică modificările înainte de commit.
  - Excepție: în jurnal, în memorie și în `agent-activity.md` poți face oricând editări mici, fără rezervare și fără să rescrii textul altora.
- **Commit-ul:** îl face un singur agent pentru un set de modificări, care îi spune celuilalt hash-ul, ca să nu-l facă și el.
- **Înainte de commit:** rulezi `git fetch` și `git status` și adaugi doar fișierele tale: `git add -- <căile tale>`, apoi `git commit -- <căile tale>`, ca să nu prinzi în commit fișiere puse în index de alt agent. Niciodată `git add -A` sau `git add .`. Fișierele din `.github/memorie/` le poți pune în commit chiar dacă au și intrări ale altor agenți.
- **Lucrul pe o ramură:** clona e comună, așa că după commit o readuci pe `master`, ca alt agent să nu facă commit pe ramura ta fără să știe. Cât timp clona e pe ramură, scrii asta în rândul tău din `agent-activity.md`.
  - Mai simplu: ramura o lucrezi într-un `git worktree`, într-un folder temporar din afara clonei (`git worktree add <folder> <ramura>`; la final, `git worktree remove <folder>`). Clona comună rămâne tot timpul pe `master`, iar commit-ul și push-ul le faci din folderul acela, cu `git -C <folder> …`.
  - Înainte de `git checkout master`, muți în afara depozitului sau ștergi folderele ignorate din `.github/surse/<proiect>/` (`.venv/`, `out/`, `__pycache__/`). `.gitignore`-ul care le ascunde există doar pe ramură, iar pe `master` ar apărea ca fișiere netrasate. De la uneltele comune, `.gitignore`-ul din rădăcină le ignoră în tot depozitul, și pe `master`.
  - Memoria și jurnalul scrise pe ramură ajung pe `master` abia la îmbinare.
  - **Aducerea în `master`.** Întâi verifici că ramura doar adaugă: `git diff --name-status master...<ramura>` nu are fișiere șterse (`D`), iar rândurile schimbate din fișierele comune sunt doar completate. Legăturile dintre variante din README-uri și scoaterea textelor „pe ramură, neîmbinat” și „proiectul vechi” le pui în commit tot pe ramură. Din clona din cloud nu poți actualiza `master` pe GitHub: și push-ul direct, și `gh pr merge` sunt refuzate („Cannot update this protected ref”), deși regula nu apare nici în setările ramurii, nici în API-ul de rulesets. N-o ocolești, nici cu `--admin`, nici cu alte unelte. Trimiți ramura, deschizi un pull request spre `master` (`gh pr create --base master --head <ramura>`), verifici că e `MERGEABLE` și `CLEAN` (`gh pr view <n> --json mergeable,mergeStateStatus`) și îi dai utilizatorului linkul. Îl îmbină el, cu „Create a merge commit”, ca toate commit-urile din jurnal să rămână în istoria lui `master`. Până atunci, clona comună rămâne pe `origin/master`: dacă ai adus commit-urile în `master` local, le trimiți cu `git push origin master:<ramura>`, verifici cu `git ls-remote --heads origin <ramura>` că ramura de pe GitHub are hash-ul lui `master` (clona aduce doar `master`, deci `origin/<ramura>` nu există) și abia apoi readuci `master` cu `git reset --keep origin/master`. După îmbinare, clona se aduce la zi cu `git fetch` și `git merge --ff-only origin/master`.
- **Sesiunile din clone diferite,** de exemplu din cloud, nu se văd între ele: rândul din „Acum”, rezervările și munca fiecăreia apar abia după push. Le vezi cu `git ls-remote origin` (ramurile și `refs/pull/N/head`), `gh pr list` și `agent-activity.md` de pe ramura fiecăreia. Clona aduce doar `master`, așa că `git fetch` lasă `origin/<ramura>` neactualizată: ramurile le aduci explicit, cu `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`. Mediul din cloud nu e permanent, așa că la final ceri acordul pentru push pe ramura ta (push-ul pe altă ramură decât `master` nu republică site-ul) și deschizi pull request-ul.
- **Fără suprascrieri la îmbinare.** Înainte să deschizi pull request-ul spre `master`, verifici, pe lângă „Aducerea în `master`”:
  1. **Planurile și imaginile existente rămân identice.** În `git diff --name-status origin/master...<ramura>`, fișierele `*.jpg`, `*.png` și `*.pdf` apar doar cu `A`. Comanda `git diff --name-status --diff-filter=DMRT origin/master...<ramura> -- '*.jpg' '*.png' '*.pdf'` nu trebuie să afișeze nimic. Un `M`, `D` sau `R` înseamnă că ramura suprascrie, șterge sau mută un plan ori o imagine deja publicată. Atunci nu deschizi pull request-ul (dacă e deschis, scrii problema în el), iar agentul ramurii își salvează rezultatul sub nume noi, lângă fișierele existente. Singura excepție e o corectură cerută de utilizator chiar pentru acel fișier, pe care o scrii în descrierea pull request-ului.
  2. **O variantă nouă** pentru un proiect existent intră în folderul proiectului, nu într-unul nou, cu literele următoare și cu fișiere cu nume noi, ca variantele C și D din „Polite viniluri/” (`propunere_C_beton_gri.jpg`, `plan_tehnic_polite_viniluri_beton.pdf`), iar sursele ei, în `.github/surse/<proiect>/<varianta>/` (vezi „Variantele noi se adaugă, nu înlocuiesc”). Nu regenerezi și nu înlocuiești planurile sau imaginile existente.
  3. **Istoria nu se rescrie:** o ramură publicată nu se rebazează, iar `git push --force` nu se folosește.
  4. **Conflictele:** când pull request-ul are conflicte, aduci `origin/master` în ramura ta, cu `git merge origin/master`. În `agent-activity.md`, `jurnal.md`, `memorie.md` și `README.md` din rădăcină păstrezi rândurile ambelor părți; „Istoric” rămâne în ordine descrescătoare după oră. La imagini și PDF-uri nu alegi o versiune peste alta: te oprești și întrebi utilizatorul.
  5. **Alt pull request deschis pe aceleași fișiere:** dacă un pull request încă neîmbinat modifică memoria sau README-urile pe care le modifici și tu, pornești ramura ta din capătul lui și scrii în descriere „se îmbină după #N”. Așa, cele două intră în `master` fără conflicte. Dacă ramura lui avansează între timp, aduci capătul nou în ramura ta, cu `git merge`, înainte de push. Dacă în capătul nou s-au mutat sau redenumit fișiere, actualizezi căile din fișierele tale care le folosesc (teste, linkuri, docstring-uri).
  6. **Site-ul se construiește.** Pull request-urile nu au verificări automate, iar publicarea pornește abia după îmbinare. Imaginile noi nu au EXIF, iar linkurile duc la fișiere existente. Dacă ai Docker, construiești site-ul cu imaginea folosită de GitHub, într-o copie temporară a ramurii: `d=$(mktemp -d) && git clone -q --branch <ramura> . "$d" && docker run --rm -v "$d":/github/workspace -e GITHUB_WORKSPACE=/github/workspace -e GITHUB_REPOSITORY=abpostelnicu/design-interior -e INPUT_SOURCE=. -e INPUT_DESTINATION=_site ghcr.io/actions/jekyll-build-pages:v1.0.13; rm -rf "$d"`. Construcția e bună dacă se termină cu „done in … seconds”. Dacă pluginul de metadate nu ajunge la API („The GitHub API credentials you provided aren't valid”, la fel și pe `master`), adaugi doar în `_config.yml`-ul copiei temporare `url: "https://abpostelnicu.github.io"` și `baseurl: "/design-interior"` și rulezi cu `--network none`.
  7. **Verificarea o scrii în pull request,** ca utilizatorul să știe ce îmbină: ce se adaugă, ce se schimbă și că planurile și imaginile existente rămân neschimbate.
  8. **După îmbinare** ramura nu se mai folosește: continui pe `master` sau pe o ramură nouă, pornită din `master`. Verifici publicarea, cu `gh run list --workflow publicare-site.yml -L 1`, și pagina proiectului.
- **Scripturile altui agent:** dacă le modifici, îi spui exact ce ai schimbat.
- **Ramura altui agent, cu sesiunea încheiată:** dacă pull request-ul lui îl conține pe al tău, iar tu ai mai adăugat commit-uri după ce sesiunea lui s-a încheiat, aduci tu capătul nou în ramura lui, cu `git merge`, și scrii în pull request-ul lui ce ai adus. Altfel, după ce se îmbină al tău, al lui rămâne cu conflicte în „Istoric” din `agent-activity.md`, unde amândouă adaugă rânduri sus.
- **Fără bucle:** nu răspunzi la o confirmare cu altă confirmare.

### Verificări înainte de livrare

- **Imaginile:** crop-uri mărite pe zonele critice. Obiectul nu trebuie să plutească, să intre în plintă sau să aibă muchii zimțate. Imaginile nu au EXIF.
- **Planul:** fără texte suprapuse; cotele parțiale dau totalul; PDF-ul e A3.
- **Markdown:**
  - toate linkurile relative duc la fișiere existente;
  - ancorele merg, de exemplu `#montaj-pas-cu-pas`;
  - pașii sunt numerotați fără goluri.
- **Prețurile:** totalurile sunt recalculate, iar fiecare link e deschis efectiv.
- **Cotele:** sunt aceleași în README, în lista de materiale, pe plan și în randări.
- **Automat:** `python -B .github/unelte/verificari.py "<Proiect>"` verifică livrabilele, metadatele imaginilor, formatul A3, linkurile relative, diacriticele, datele personale și calculele din lista de materiale. Trebuie să dea 0 probleme; avertismentele le citești pe rând.

## Lecții învățate

- **2026-10-29 · Cuier hol:** prima propunere era pe partea greșită a ferestrei și avea o bancă necerută. Confirmă peretele și componentele înainte de randare.
- **2026-10-29 · Cuier hol:** formularul pentru cote a rămas necompletat, așa că propunerea s-a făcut pe estimări și s-a refăcut după măsurători. Cere cotele devreme, dar nu bloca lucrul.
- **2026-10-29 · Cuier hol:** cu tavanul măsurat (270 cm) ca scară, cotele estimate din poza calibrată au ieșit la mai puțin de 2 cm de cele măsurate. Cu tavanul presupus (280 cm), toate ieșeau cu ~4 % mai mari: partea de sus a golului ferestrei ~242 în loc de 231,5 cm. Prima cotă de cerut e înălțimea tavanului, pentru că dă scara întregii fotografii.
- **2026-10-29 · Cuier hol:** panoul înalt de 2 m arăta tăiat scurt lângă fereastră. Aliniat cu partea de sus a golului ferestrei, arată bine.
- **2026-10-29 · Cuier hol:** șuruburile din cutia cârligelor sunt prea scurte pentru panoul de ~2 cm. Cârligele se prind cu șuruburi Spax de 4,5 × 60 mm, în dibluri DuoPower de 6 × 30 mm. Socotește lungimea șurubului: talpa piesei, placarea și adâncimea în perete.
- **2026-10-29 · Cuier hol:** panouri riflaj negre de 60 cm lățime nu s-au găsit, doar de 40 cm. Verifică devreme dimensiunile standard pentru varianta B.
- **2026-10-29 · Cuier hol:** panouri-riflate.ro taie gratuit panourile la dimensiune.
- **2026-10-29 · Cuier hol:** un subagent de cercetare a scris lista de cumpărături în engleză. Rescrie în română tot ce primești în altă limbă, înainte să salvezi.
- **2026-10-29 · Depozit:** depozitul avea în nume adresa casei. A fost refăcut public, cu numele `design-interior`, cu istoricul rescris și cu emailul noreply.
- **2026-10-29 · Depozit:** amintirile Copilot salvate când depozitul avea vechiul nume nu au mai apărut în depozitul nou. De aceea memoria completă stă în fișierele din `.github/memorie/`, iar în Copilot Memory intră doar regulile importante.
- **2026-10-29 · Peretele cu televizorul:** agentul nu a găsit note de la proiectele anterioare și a dat de scripturile cuierului abia în folderul temporar al altei sesiuni. De aceea scripturile fiecărui proiect se păstrează în `.github/surse/<proiect>/`, iar tiparul de design, în această memorie.
- **2026-10-29 · Depozit:** o informare trimisă cu `send_message` la trei sesiuni inactive le-a pornit pe toate trei din nou. Rezervările se țin de aceea în [agent-activity.md](agent-activity.md), unde le văd toți fără să fie deranjați; mesajele merg doar la agenții care lucrează chiar acum.
- **2026-10-29 · Depozit:** utilizatorul vrea să vadă într-un singur loc ce face fiecare agent, așa că fiecare agent își trece activitatea în [agent-activity.md](agent-activity.md).
- **2026-10-29 · Polițe viniluri:** fără tavan măsurat, camera s-a calibrat pe obiecte cu dimensiuni din fișele producătorilor (televizorul, comoda) și pe lățimea peretelui, cu tavanul lăsat necunoscut. Așa s-a văzut că înălțimea dată (250 cm) nu se potrivește cu poza (~262 cm). Poziționează obiectele noi față de obiecte cunoscute (aici, televizorul), nu față de tavan.
- **2026-10-29 · Polițe viniluri:** ecranul aprins al televizorului arăta numele rețelelor Wi-Fi din jur, iar prin ușă se vedea o persoană. Înainte de publicare stingi ecranele și scoți persoanele, documentele și orice text din fotografie; vezi `curata_foto.py` din [.github/surse/polite-viniluri/](../surse/polite-viniluri/README.md).
- **2026-10-29 · Polițe viniluri:** un disc de vinil are 31,4 × 31,4 cm. Polițele pentru viniluri au ≥ 33 cm adâncime și ≥ 8 cm liberi deasupra discurilor. Polițele de perete obișnuite (Cioata Wally: 23 cm) sunt prea înguste, iar pe o poliță deschisă discurile au nevoie de opritoare la capete.
- **2026-10-30 · Polițe viniluri:** prima propunere avea corpuri închise de 80 × 79 × 38 cm, cu compartimente; utilizatorul le-a respins ca fiind „cutii”. Când cere polițe, propune întâi polițe flotante (linii orizontale de stejar), nu corpuri.
- **2026-10-30 · Polițe viniluri:** un perete de ~4,2 m încape pe A3 la 1:15 (~316 mm), cu planul dedesubt, dacă secțiunea, detaliile și notele stau într-o coloană de ~88 mm în dreapta. Detaliile pot fi la 1:3 sau 1:5.
- **2026-10-30 · Polițe viniluri:** utilizatorul a respins orice consolă la vedere, chiar și cele simple, negre, din varianta B: vrea polițele prinse direct în perete. Prinderea ascunsă pe tije M12 în ancoră chimică încape într-o poliță de 4 cm, dar verifică tijele în cazul cel mai rău (polița stă doar în tije): la 33 cm adâncime și ~38 kg, 3 tije M12 de clasa 4.8 lasă o rezervă de numai ~1,45, iar 4 tije, ~1,9 (`rod_check()` din `polite-viniluri/design.py`).
- **2026-10-30 · Polițe viniluri:** „suport” e ambiguu: opritoarele de cărți se vând ca „suport de carte”, iar consolele, ca „suport pentru raft”. La „să nu aibă suporții negri” am scos consolele, dar am îmbrăcat în stejar și opritoarele din propunerea principală, ca să nu rămână nimic negru; opritoarele negre au trecut în varianta B. Când cuvântul poate însemna două piese, acoperă ambele sensuri și spune-i utilizatorului cum l-ai înțeles.
- **2026-10-30 · Polițe viniluri:** în randări, copertele maro sau galbene de la capătul rândului de discuri par opritoare de stejar: dă-le culori neutre sau reci. Discurile și texturile de lemn folosesc generatoare aleatoare separate, ca discurile să rămână identice în A și B.
- **2026-10-29 · Polițe viniluri:** randarea pieselor cu multe fețe care se acoperă (polițe, discuri, opritoare) merge mai sigur cu buffer de adâncime (`Canvas.face` din `polite-viniluri/core.py`) decât cu ordine de desenare. Obiectele din poză care stau în fața celor noi (de exemplu boxele) se desenează doar în bufferul de adâncime.
- **2026-10-29 · Polițe viniluri:** prețuri: Hornbach blochează și el descărcarea automată („Client Challenge”). La Dedeman, `curl` pe pagina produsului merge; prețul din `itemprop="price"` poate fi pe cutie, iar ambalajul apare la „Se livrează la: cutie (50 buc)”. Un subagent de cercetare cu 11 cerințe a rulat peste o oră fără rezultat: verifică direct prețurile esențiale și dă-i subagentului cerințe puține și precise.
- **2026-10-29 · Polițe viniluri:** Cioata face mobilier la comandă: personalizează dimensiunea și finisajul lemnului, cu livrare în 2–8 săptămâni, dar nu montează pe perete. Mobilierul asortat cu o piesă Cioata se cere întâi de la ei.
- **2026-10-30 · Polițe viniluri beton:** internetul public a fost blocat în mediul de lucru. `curl` dădea 000, `web_fetch` nu găsea adresele, Playwright dădea `ERR_BLOCKED_BY_CLIENT`, iar `web_search` a dat eroare la toți cei 4 subagenți de cercetare (inspirație, tehnică, prețuri), după 10–35 de încercări fiecare, în ~30 de minute. Încearcă tu o dată `web_search` și `curl` pe un magazin înainte să lansezi subagenți de cercetare. Dacă nu merg, nu-i lansa: prețurile noi le treci „de verificat”, iar la cele vechi scrii data ultimei verificări.
- **2026-10-30 · Polițe viniluri beton:** revizuirea conceptului cu un agent rubber-duck, înainte de randări, a prins probleme de montaj:
  - un ansamblu rigid pe 8 tije nu intră pe tije, pentru că gaura Ø13 la M12 lasă un joc de 0,5 mm;
  - tijele puse direct în MDF ovalizează gaura;
  - cepurile lipite peste lac nu țin.

  Când legi polițele cu verticale, fiecare poliță se montează separat, pe tijele ei. Verticala se lipește în atelier de o singură poliță, pe lemn curat, iar la cealaltă rămâne un rost de umbră de 3 mm. Tijele le verifici cu discurile ticsite, iar ancora, la smulgere: `rod_check()` și `rod_pull()` din `polite-viniluri/beton/design.py`.
- **2026-10-30 · Polițe viniluri beton:** pentru polițe din beton decorativ se folosește microciment de ~2 mm pe un miez ușor, nu beton turnat.
  - Miezul e din placaj de mesteacăn, iar canalele tijelor se frezează înainte de lipirea plăcilor.
  - O placă GFRC de 80 × 33 × 4 cm ar avea ~22 kg, față de ~8,5 kg.
  - Muchiile se rotunjesc (R3), plasa trece peste muchii, lacul e poliuretanic bicomponent, iar spatele se sigilează.

  Textura de microciment pentru randări o dă `beton.py` din [.github/surse/polite-viniluri/beton/](../surse/polite-viniluri/beton/README.md), cu tonurile „gri” și „antracit” (antracitul are ΔE ~0,4 față de fronturile comodei).
- **2026-10-30 · Polițe viniluri beton:** când mai mulți subagenți folosesc în paralel același `design.py`, nu redenumi și nu șterge chei sau funcții. Aici, `drawing.py` folosea încă `D["dowel_len"]`. Adaugi cheile noi lângă cele vechi și le spui agenților ce s-a schimbat.
- **2026-10-30 · Polițe viniluri beton:** în planul A3, notele scrise rând cu rând ieșeau din pagină sau peste desene.
  - În `polite-viniluri/beton/drawing.py`, notele sunt paragrafe, iar `wrap()` le rupe pe lățimea coloanei, măsurând textul cu fontul real. Cifrele rămân lipite de unități.
  - După fiecare schimbare din plan, rulezi `verifica_plan.py`, din același folder: găsește textele ieșite din pagină, suprapuse sau intrate în desene și indicațiile care trec prin texte.
  - La adnotări măsori doar textul, cu `Text.get_window_extent(t, renderer)`; `Annotation.get_window_extent` include și linia de indicație și dă suprapuneri false.
- **2026-10-30 · Depozit:** sesiunea de supraveghere nu a văzut celelalte sesiuni: în cloud, fiecare are clona ei, iar `list_agents` și `gh agent-task list` nu le arată. Munca lor se vede doar pe GitHub, după push: `git ls-remote origin` (ramurile și `refs/pull/N/head`), `gh pr list` și `agent-activity.md` de pe fiecare ramură. Așa s-a văzut că, în timp ce supravegherea își pregătea regulile pe vechiul `master`, sesiunea ramurii `polite-viniluri-beton` adăugase 2 commit-uri și deschisese PR #1, cu modificări în aceleași fișiere din memorie. Rulezi `git fetch` din nou chiar înainte să modifici fișierele comune, chiar dacă ai verificat cu câteva minute înainte. Clona aduce doar `master`, așa că ramurile altora le aduci explicit: un `git fetch` simplu a lăsat `origin/polite-viniluri-beton` la capătul vechi, fără niciun avertisment, iar două commit-uri noi ale ramurii s-au văzut doar în `git ls-remote`.
- **2026-10-30 · Depozit:** când schimbi o regulă, o cauți în toate fișierele care o repetă, nu doar în cel în care ai găsit-o: `git grep -n -i '<cuvinte din fraza veche>' -- .github README.md`.
  - Regulile stau în `memorie.md`, iar rezumatul lor e și în `.github/copilot-instructions.md` și în fișierul agentului, pe care agenții le citesc primele.
  - Supravegherea a corectat regula folderului separat doar în pasul 2 din `memorie.md`. Fraza veche, „o variantă nouă stă în folderul ei”, a rămas în celelalte două fișiere, până când a corectat-o sesiunea din beton.
- **2026-10-30 · Polițe viniluri beton:** am pus varianta din beton într-un folder nou, „Polite viniluri beton/”, iar utilizatorul a corectat: „totul ar trebui băgat în același folder în care sunt și polițele din stejar”. O variantă nouă pentru un proiect existent intră în folderul lui:
  - literele continuă: după A și B vin C și D, în texte, în etichetele comparației și pe plan („varianta C”, ca să nu se confunde cu „detaliul C”);
  - fișierele au nume noi, cu sufix (`propunere_C_beton_gri.jpg`, `plan_tehnic_polite_viniluri_beton.pdf`, `lista_materiale_beton.md`), iar cele existente rămân identice;
  - README-ul proiectului primește o frază la început, rânduri noi în tabelul cu fișiere și o secțiune la final. Titlurile din secțiune nu le repetă pe cele existente, ca ancorele să nu se dubleze (de exemplu „Montaj pas cu pas pentru C și D”), iar tabelele comune, ca „Ce e acum pe perete”, nu se copiază: se trimite la ele;
  - sursele stau într-un subfolder, `.github/surse/polite-viniluri/beton/`.

  Mutarea s-a făcut cu `git mv`. Randările nu au text, deci au rămas aceleași; comparația și planul, care aveau etichetele A și B, s-au regenerat. Ca probă, randările refăcute după redenumire au ieșit identice octet cu octet, iar planul nou diferă de cel vechi doar în zonele cu etichete.
- **2026-10-30 · Depozit:** fiecare proiect își copia scripturile de la cel dinainte și le schimba pe drum, iar greșelile treceau odată cu ele: `sample` din `polite-viniluri/materials.py`, copiat identic și în sursele variantelor din beton, întorcea textura în oglindă. Uneltele sunt acum adunate și testate în [.github/unelte/](../unelte/README.md). Un proiect nou le importă, iar o unealtă care folosește și altor proiecte intră acolo, cu test.
- **2026-10-30 · Depozit:** o calibrare doar pe muchii din planul peretelui a dat o distanță focală de 7 px, cu aparatul la 3 cm de perete, deși eroarea era mică (0,58 px). Calibrarea folosește doar dreptele pe care stau segmentele, nu capetele lor: scara vine din distanțele dintre drepte paralele, iar distanța până la aparat, din muchii care ies din perete, ca laturile comodei. Verifică și distanța focală (de obicei 0,5–0,9 × lățimea fotografiei) și poziția aparatului, nu doar eroarea RMS.
- **2026-10-30 · Depozit:** sesiunea uneltelor a pornit din `master` și a trimis ramura `unelte-agenti` fără să mai verifice `gh pr list`; între timp apăruse PR #2, cu regulile „Fără suprascrieri la îmbinare” și cu modificări în aceleași fișiere din memorie. Ramura era deja publicată, așa că nu s-a rebazat: capătul lui #2 a intrat în ea cu `git merge`, iar în jurnal și în `agent-activity.md` au rămas rândurile tuturor. Înainte de push și de pull request rulezi din nou `gh pr list` și `git ls-remote origin`, chiar dacă ai verificat la început. Verifici și după ce ai deschis pull request-ul, înainte de fiecare push, până închei sesiunea: aici #2 a mai avansat de două ori, o dată cu o mutare de fișiere care a cerut căi noi în unelte (pasul 5).
- **2026-10-31 · Polițe viniluri beton:** pe calculatorul utilizatorului, internetul merge, cu `web_search`, `curl` și browserul integrat. Hornbach a răspuns și la `preturi.py`, deși pe 29.10 dădea „Client Challenge”: blocarea vine și trece. eMAG a dat captcha („Am detectat trafic neobișnuit de mare”, HTTP 511) după ce trei subagenți de cercetare și `preturi.py` au cerut pagini în același timp, iar după vreo oră a mers din nou în browser. Captcha nu se ocolește; le spui subagenților să nu mai ceară pagini de la magazinul care blochează.
- **2026-10-31 · Polițe viniluri beton:** trei subagenți de cercetare în paralel (ateliere, sisteme de microciment, feronerie), cu cerințe puține și precise, au terminat în 9–14 minute. Rezultatele lor le verifici, nu doar prețul, ci și potrivirea: un subagent a propus o folie de mascare pentru zugrăveli ca „folie de protecție pentru mobilă” și un manșon-sită prea mic. Un rezumat din `web_search` a dat un link Fischer care nu există (404): deschizi orice link înainte să intre în listă.
- **2026-10-31 · Polițe viniluri beton:** feroneria pentru tije M12 ascunse:
  - tijele M12 de clasa 8.8 nu le-am găsit la Dedeman (tija lor M12 de 1 m e de clasa 4.8); le au Hornbach (DIN 975, 8.8) și magazinele de feronerie online, ca Alsafix;
  - manșoanele-sită Fischer FIS H K se aleg după tijă și după cât intră tija în perete: 16 × 85 e pentru M8–M10; pentru M12 sunt 20 × 85 (ancorare 85 mm, gaură Ø20 × 90 mm) și 20 × 130 (ancorare 130 mm, gaură Ø20 × 135 mm, 25 ml de mortar). Dedeman are doar 16 × 85, Hornbach 20 × 85, iar 20 × 130 l-am găsit la Malinco;
  - când tijele se prind în două reprize, la ore distanță, îți trebuie două mixere: ancora se întărește în mixer, iar cartușul se refolosește doar cu unul nou. Cartușul Den Braven de 300 ml de la Dedeman vine cu două.
- **2026-10-31 · Polițe viniluri beton:** Cioata face în Târgu Mureș linia Veneto, din stejar și microciment pus pe MDF, cu un singur ton de microciment în paletar, „C9 - antracit spre negru”, și personalizează dimensiunile. Pentru piese asortate cu Veneto e primul de întrebat; pentru alt ton și pentru miez din placaj se cere special. Are showroom-uri în București (Băneasa) și în Târgu Mureș.
- **2026-10-31 · Depozit:** clona locală comună aduce toate ramurile (`remote.origin.fetch = +refs/heads/*:refs/remotes/origin/*`); doar clona din cloud aducea numai `master`. Ramura nouă am pornit-o din `origin/master` într-un worktree din afara clonei (`git worktree add -b <ramura> <folder> origin/master`), fără să ating clona, care rămăsese în urma lui `origin/master` și avea munca necomisă a altor agenți. Scoate legătura ramurii cu `origin/master` (`git branch --unset-upstream`), ca un `git push` simplu să nu țintească `master`.

## Proiecte

| Proiect | Folder | Stare | Surse | Sesiunea care îl lucrează |
|---|---|---|---|---|
| Cuier hol | [Cuier hol](../../Cuier%20hol/README.md) | Gata: panou riflaj din stejar de 44 × 223,5 cm, așezat pe plintă, cu 5 cârlige negre mat | [.github/surse/cuier-hol/](../surse/cuier-hol/README.md) | Propunere cuier pentru fereastră |
| Polițe viniluri (peretele cu televizorul) | [Polite viniluri](../../Polite%20viniluri/README.md) | Gata: 2 polițe flotante din stejar de 80 × 33 × 4 cm, doar în dreapta televizorului, prinse direct în perete pe câte 4 tije M12 ascunse, fără console; A cu opritoare îmbrăcate în stejar, B cu opritoare negre. Înainte de comandă rămân de verificat: tavanul, peretele, finisajul comodei, ușa din dreapta și cablurile | [.github/surse/polite-viniluri/](../surse/polite-viniluri/README.md) | amenajare perete TV cu polite |
| Polițe viniluri, variantele C și D: beton decorativ și stejar (peretele cu televizorul) | [Polite viniluri](../../Polite%20viniluri/README.md#variantele-c-și-d-beton-decorativ-și-stejar), lângă A și B | Variante în plus, în același folder cu cele din stejar, cu fișiere noi, fără să le înlocuiască; în `master` din [pull request-ul #1](https://github.com/abpostelnicu/design-interior/pull/1): aceleași 2 polițe, din microciment pe placaj, legate de o verticală din stejar masiv; C beton gri, D beton antracit. Prețurile și căile de procurare sunt verificate pe 31.10.2026, în [pull request-ul #4](https://github.com/abpostelnicu/design-interior/pull/4), pe care îl îmbină utilizatorul: Cioata întâi, apoi ateliere de microciment sau un tâmplar cu un set, plus feroneria. Prețul polițelor se află din ofertă | [.github/surse/polite-viniluri/beton/](../surse/polite-viniluri/beton/README.md) | Polițe viniluri beton și stejar; prețurile: actualizare politelor de beton |
