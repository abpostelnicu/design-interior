# Memoria comună a agenților

Aici agenții care lucrează în acest depozit păstrează ce au învățat, ca agentul următor să nu pornească de la zero. Orice agent citește acest fișier înainte de un proiect de amenajare și îl actualizează la final. Ce a făcut fiecare sesiune, pe scurt, e în [jurnal.md](jurnal.md). Proiectele noi le face agentul [Designer interior](../agents/designer-interior.agent.md).

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
- **Proiecte executabile cu materiale din comerț**, cu prețuri estimative și linkuri.
- **Montaj pas cu pas foarte detaliat.**
- **Fără elemente adăugate din proprie inițiativă.** A respins banca de la cuier. Extra-urile apar doar ca opțiuni în text.
- **Stil și materiale:** stejar natur și negru mat. Tâmplăria și ușa de intrare sunt negre sau antracit. Polițele de pe peretele cu televizorul trebuie să fie din stejar, asortate cu finisajul comodei.
- **Cote:** le dă ca listă numerotată, uneori doar cifre în mm. Scrie-i cum le-ai interpretat.
- **Commit și push:** de obicei le cere explicit, la final. Fiecare push pe `master` republică site-ul public.
- **Agenți în paralel:** lucrează des cu mai mulți agenți deodată și vrea ca ei să se coordoneze și să urmeze același tipar de design.
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
- Pe peretele din dreapta ferestrei, estimat din poză: un senzor la ~2,0 m, un termostat în colț la ~1,25 m, un întrerupător la ~0,8 m și o priză la ~0,25 m.
- Proiect: „Cuier hol”.

### Peretele cu televizorul

- Peretele: 419 cm lățime și 250 cm înălțime.
- Televizorul: TCL 98C8L, 98".
- Comoda TV: Cioată Veneto, 242 cm lățime și 67 cm înălțime ([pagina produsului](https://www.cioata.eu/comoda-tv-veneto-242cm.html)).
- Boxele: centru Klipsch RP-504C II; de podea Klipsch RP-8000F II.
- Cerința: polițe integrate în perete pentru viniluri, din stejar, asortate cu comoda.
- Proiect: în lucru, în folder separat.

## Tiparul de design

Tiparul a fost stabilit la proiectul „Cuier hol”, care rămâne referința ([pagina de pe site](https://abpostelnicu.github.io/design-interior/Cuier%20hol/)). Fiecare proiect nou trebuie să arate și să fie documentat la fel. Scripturile, cum le rulezi și cum le adaptezi sunt în [.github/surse/cuier-hol/](../surse/cuier-hol/README.md).

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

1. **Fotografia.** O salvezi ca JPEG de 768 × 1024 cu PIL, ca să nu păstreze metadatele (vezi „Depozitul și site-ul”). Faci zoom-uri cu grilă de coordonate pe zona de lucru și notezi tot ce contează:
   - prize, întrerupătoare, senzori, termostat;
   - balamalele și sensul de deschidere al ușilor;
   - plinte, glafuri, rame.
2. **Calibrarea camerei** (`camera.py`). Din muchiile drepte ale camerei obții un model al aparatului foto. Cu el estimezi cote reale direct din poză: lățimi de perete, înălțimi, poziția prizelor. Scara vine din înălțimea tavanului: întâi o presupui, apoi o înlocuiești cu valoarea măsurată.
3. **Constrângerile.**
   - Ușile: în ce parte se deschid și cât loc rămâne la 90°, inclusiv mânerul.
   - Prizele și întrerupătoarele: le eviți sau faci decupaje.
   - Senzorii și termostatul nu se acoperă.
   - Plinta nu se taie.
   - Aliniamentele cu liniile existente: partea de sus a golului ferestrei, capul ușii, glaful.
4. **Designul.** Faci exact ce s-a cerut. Elementele în plus, cum ar fi o bancă sau o bandă LED, apar doar ca opțiuni în text, nu în randare.
5. **Randările** (`render.py`) și **comparația** (`compare.py`). Verifici rezultatul cu crop-uri mărite pe margini, pe contactul cu plinta sau pardoseala și pe feronerie.
6. **Planul tehnic** (`drawing.py`). Verifici, cu crop-uri din PNG-ul la 220 dpi, că textele nu se suprapun, și că PDF-ul e A3: `/MediaBox [ 0 0 1190.55 841.89 ]`.
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
   - Dedeman afișează prețul fără localitate, dar stocul abia după ce alegi localitatea.
   - Leroy Merlin blochează descărcarea automată a paginilor (403).
   - Verifici că feroneria se potrivește peretelui. La cărămidă: dibluri Fischer DuoPower Ø6 și șuruburi destul de lungi ca să treacă prin panou până în perete.
10. **Montajul pas cu pas**, în `README.md`-ul proiectului.
    - Îl scrii pentru cineva care face singur montajul.
    - Conține ordinea operațiilor, cotele de montaj, uneltele, adâncimile de găurit (cu bandă pe burghiu), timpii adezivului, cum se taie fără să se ciupească furnirul și verificările finale.
11. **Verificările, commit-ul și push-ul**, ca mai jos.

### Scripturile

Sunt în [.github/surse/cuier-hol/](../surse/cuier-hol/README.md), cu instrucțiuni de rulare și de adaptare la o fotografie nouă. Pentru un proiect nou copiezi folderul în `.github/surse/<proiect>/`, cu numele fără diacritice și cu cratimă între cuvinte, și îl adaptezi acolo. Nu modifici scripturile altui proiect.

Mediul Python: `python3 -m venv .venv && .venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy`. Python-ul sistemului nu are numpy. Rezultatele se generează în `out/`, care nu intră în depozit, apoi se copiază în folderul proiectului cu numele finale.

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
  - În depozit pui doar imagini generate sau salvate din nou cu OpenCV sau PIL, care nu păstrează metadatele EXIF. Fotografia de lucru din `.github/surse/<proiect>/original.jpg` se salvează așa: `ImageOps.exif_transpose(Image.open(sursa)).convert("RGB").resize((768, 1024)).save("original.jpg", quality=95)`.
- **Căile absolute** de pe calculator nu apar în fișiere: numele folderului local conține date personale.
- **Adresa de email:** commit-urile se fac cu adresa „noreply” de la GitHub, care e deja setată local în depozit. Verifici cu `git config user.email`.
- **Mesajele de commit:** în română, la imperativ, de exemplu „Adaugă…” sau „Așază…”. La final pui rândul `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
- **Semnătura GPG.** Configurația globală cere commit-uri semnate, dar parola se introduce într-o fereastră pinentry pe care un agent nu o poate completa. Utilizatorul a aprobat commit-uri nesemnate pentru acest depozit, așa că folosești `git -c commit.gpgsign=false commit …`. Opțiunea se pune doar pe comandă; configurația nu se modifică.
- **Fără arhive:** în depozit nu se păstrează variante vechi; utilizatorul a cerut ștergerea arhivei. `.DS_Store` e ignorat.
- **Site-ul:** <https://abpostelnicu.github.io/design-interior/> se publică automat la fiecare push pe `master`.
  - Linkurile rămân relative; spațiile din numele folderelor se scriu `%20`.
  - Orice folder cu `README.md` apare singur în meniul site-ului. Folderele care încep cu punct, ca `.github/`, nu se publică.
  - Imaginea afișată când se trimite linkul este `imagine_implicita` din `_config.yml`.

### Coordonarea între agenți

- **Foldere proprii:** fiecare agent lucrează în folderul proiectului său. Un proiect aparține sesiunii care l-a început, până când utilizatorul spune altfel.
- **Fișiere comune:** `README.md` din rădăcină, `_config.yml`, `_layouts/`, `assets/` și `.github/`, inclusiv această memorie.
  - Înainte să le modifici, anunți agenții activi cu `send_message` și ceri exclusivitate: „până îți confirm că am terminat, modific doar eu X”.
  - Cel care primește anunțul nu editează acele fișiere, nu rulează scripturile care le regenerează și nu face commit până nu primește „Am terminat”.
  - Când termini, trimiți „Am terminat” și spui pe scurt ce ai schimbat. Celălalt verifică modificările înainte de commit.
  - Excepție: în jurnal și în memorie poți adăuga oricând o intrare scurtă, cu o editare mică, fără să rescrii textul altora.
- **Commit-ul:** îl face un singur agent pentru un set de modificări, care îi spune celuilalt hash-ul, ca să nu-l facă și el.
- **Înainte de commit:** rulezi `git fetch` și `git status` și adaugi doar fișierele tale: `git add -- <căile tale>`, apoi `git commit -- <căile tale>`, ca să nu prinzi în commit fișiere puse în index de alt agent. Niciodată `git add -A` sau `git add .`.
- **Scripturile altui agent:** dacă le modifici, îi spui exact ce ai schimbat.
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

## Lecții învățate

- **2026-10-29 · Cuier hol:** prima propunere era pe partea greșită a ferestrei și avea o bancă necerută. Confirmă peretele și componentele înainte de randare.
- **2026-10-29 · Cuier hol:** formularul pentru cote a rămas necompletat, așa că propunerea s-a făcut pe estimări și s-a refăcut după măsurători. Cere cotele devreme, dar nu bloca lucrul.
- **2026-10-29 · Cuier hol:** cotele estimate din poza calibrată au ieșit la mai puțin de 2 cm de cele măsurate.
- **2026-10-29 · Cuier hol:** panoul înalt de 2 m arăta tăiat scurt lângă fereastră. Aliniat cu partea de sus a golului ferestrei, arată bine.
- **2026-10-29 · Cuier hol:** șuruburile din cutia cârligelor sunt prea scurte pentru panoul de ~2 cm. Cârligele se prind cu șuruburi Spax de 4,5 × 60 mm, în dibluri DuoPower de 6 × 30 mm. Socotește lungimea șurubului: talpa piesei, placarea și adâncimea în perete.
- **2026-10-29 · Cuier hol:** panouri riflaj negre de 60 cm lățime nu s-au găsit, doar de 40 cm. Verifică devreme dimensiunile standard pentru varianta B.
- **2026-10-29 · Cuier hol:** panouri-riflate.ro taie gratuit panourile la dimensiune.
- **2026-10-29 · Cuier hol:** un subagent de cercetare a scris lista de cumpărături în engleză. Rescrie în română tot ce primești în altă limbă, înainte să salvezi.
- **2026-10-29 · Depozit:** depozitul avea în nume adresa casei. A fost refăcut public, cu numele `design-interior`, cu istoricul rescris și cu emailul noreply.
- **2026-10-29 · Depozit:** amintirile Copilot salvate când depozitul avea vechiul nume nu au mai apărut în depozitul nou. De aceea memoria completă stă în fișierele din `.github/memorie/`, iar în Copilot Memory intră doar regulile importante.
- **2026-10-29 · Peretele cu televizorul:** agentul nu a găsit note de la proiectele anterioare și a dat de scripturile cuierului abia în folderul temporar al altei sesiuni. De aceea scripturile fiecărui proiect se păstrează în `.github/surse/<proiect>/`, iar tiparul de design, în această memorie.

## Proiecte

| Proiect | Folder | Stare | Surse |
|---|---|---|---|
| Cuier hol | [Cuier hol](../../Cuier%20hol/README.md) | Gata: panou riflaj din stejar de 44 × 223,5 cm, așezat pe plintă, cu 5 cârlige negre mat | [.github/surse/cuier-hol/](../surse/cuier-hol/README.md) |
| Peretele cu televizorul | Folder nou, încă necreat | În lucru: polițe din stejar pentru viniluri | – |
