# Sursele imaginilor din „Comodă birou”

Scripturile din acest folder generează randările, imaginea de comparație, alternativa Cioata Galla 120 și planul tehnic din [`Comoda birou/`](../../../Comoda%20birou/). Folderele care încep cu punct nu apar pe site.

Tiparul general al proiectelor e în memoria comună: [`.github/memorie/memorie.md`](../../memorie/memorie.md). Scripturile de aici au fost scrise înainte ca trusa comună [`.github/unelte/`](../../unelte/README.md) să ajungă în `master` și sunt de sine stătătoare. Pornesc de la cele din [`polite-viniluri/`](../polite-viniluri/README.md), cu buffer de adâncime, cu două diferențe: camera e calibrată pe tavan, pe plan și pe birou, iar umbrele cad și pe pardoseală. Rămân așa, pentru că reproduc imaginile publicate, octet cu octet. Ce aveau general a intrat în trusă: planul PDF (`plan_pdf.py`), ușile de mobilier (`usi.py`, din `door_check`), scanarea tavanului (`camera.profil`), furnirul și riflajul (`materiale.veneer` și `materiale.reeding`, testate că dau aceleași valori ca `materials.py`) și trimiterea la detalii (`plan.callout`). Un proiect nou pornește de la trusă, nu de la aceste scripturi.

## Fișiere

| Fișier | Rol |
|---|---|
| `original.jpg` | Fotografia biroului, 311 × 554 px, salvată cu PIL, fără metadate. În ea nu apar persoane, ecrane aprinse sau texte |
| `segments.json` | Segmentele de dreaptă din fotografie, grupate pe muchii (tavanul, golul ferestrei, pardoseala, plinta, blatul și picioarele biroului), plus trei colțuri ale blatului, ca puncte |
| `camera.py` | Calibrează aparatul foto și salvează `camera.json` |
| `design.py` | Sursa unică pentru cote: `SITE` (camera, cu estimările marcate `# est.`), `DESK` (biroul), `EL` (comoda), așezarea (`GAP_DESK`, `GAP_WALL`, `Layout`) și prinderea anti-răsturnare (`ANCHOR_Y`, șurubul) |
| `core.py` | Baza randării: camera la rezoluția de lucru, `Canvas.face` și `Canvas.box` (fețe texturate cu buffer de adâncime; cu `color=None` doar ascund, de exemplu biroul din poză), `Canvas.multiply_plane` (umbre pe perete sau pe pardoseală) și `wall_light_map` (lumina peretelui din poză) |
| `materials.py` | Furnirul de stejar (fibra dreaptă, cu raze), riflajul fronturilor și culorile, citite din imaginile producătorului |
| `render.py` | Randează propunerea A (stejar natur) și varianta B (stejar închis), plus `out/acum.jpg` |
| `render_galla.py` | Randează alternativa Cioata Galla 120 (Natural Oak, contrast Nero), centrată în peretele liber, și verifică deschiderea ușilor (`door_check`) |
| `compare.py` | Face imaginea cu trei panouri: Acum, A, B (după `render.py`) |
| `drawing.py` | Desenează planul tehnic A3: vederea frontală, planul și secțiunea la 1:15, detaliile A (anti-răsturnare) și B (plinta) la 1:5, planul camerei la 1:50 și notele |

## Cum regenerezi imaginile

```sh
cd ".github/surse/comoda-birou"
python3 -m venv .venv
.venv/bin/pip install pillow numpy matplotlib opencv-python-headless scipy
.venv/bin/python camera.py         # camera.json (eroare medie ~0,55 px)
.venv/bin/python render.py         # out/propunere_A_stejar.jpg, out/varianta_B_stejar_inchis.jpg și out/acum.jpg
.venv/bin/python render_galla.py   # out/alternativa_cioata_galla_120.jpg și verificarea ușilor
.venv/bin/python compare.py        # out/comparatie_acum_vs_propuneri.jpg (după render.py)
.venv/bin/python drawing.py        # out/plan_tehnic_comoda_birou.pdf și .png
cp out/propunere_A_stejar.jpg out/varianta_B_stejar_inchis.jpg out/alternativa_cioata_galla_120.jpg \
   out/comparatie_acum_vs_propuneri.jpg out/plan_tehnic_comoda_birou.pdf out/plan_tehnic_comoda_birou.png \
   "../../../Comoda birou/"
```

`.venv/bin/python design.py` afișează cotele derivate: peretele liber, unde stă comoda, înălțimile sertarelor, gaura din perete și cât intră șurubul în ea.

## Calibrarea

Ce se știe sigur:
- tavanul are 250 cm (dat de utilizator);
- golul ferestrei Fe-06 începe la 278,9 cm de colț (din planul etajului, scalat pe cota de 327 cm; PDF-ul e la ~1:52,2, nu la 1:50 cât scrie în cartuș);
- blatul biroului Secretlab MAGNUS Pro are 150 × 70 cm (fișa producătorului).

Camera și pozițiile biroului (capătul, distanța de perete, înălțimea blatului, axele picioarelor) ies din potrivirea segmentelor. Picioarele sunt drepte verticale cu X necunoscut și Z fixat la mijlocul adâncimii blatului. Cu X și Z amândouă libere, o verticală nu e determinată: prima calibrare a dat valori de ordinul 10⁵ cm. Rezultatul are eroarea medie de 0,55 px și cea maximă de 1,95 px. Biroul iese la ~126,2 cm de colț, cu blatul la ~75,8 cm.

```sh
.venv/bin/python camera.py tavan   # scanează tavanul între 230 și 270 cm
```

Tavanul nu reiese din fotografie. Colțul camerei nu se vede, iar biroul are dimensiuni cunoscute, dar poziție liberă. Cu tavanul fixat la 230, 250 sau 270 cm, eroarea rămâne aceeași, 0,5476 px, și se mută doar biroul: de la −38 la +33 cm față de perete și de la 146 la 106 cm față de colț. Scara vine deci din tavanul dat. Verificarea se face pe o presupunere fizică: biroul pare lipit de perete, iar lipit de tot ar fi la un tavan de ~251,4 cm, deci 250 se potrivește. Pentru că fiecare centimetru de tavan mută biroul cu ~1 cm de-a lungul peretelui, peretele liber dintre colț și birou se măsoară. Calculul cu tavanul liber nu ajută, nici cu limite: rămâne lângă valoarea de pornire, iar fără limite metoda `lm` poate fugi într-o soluție în spatele aparatului, cu tavanul negativ.

Colțul camerei nu se vede: marginea din stânga a fotografiei e la ~30 cm de el. De aceea peretele liber dintre colț și birou (~126,2 cm) trebuie măsurat înainte de comandă.

## Coordonatele

Toate cotele sunt în cm:
- **X** e de-a lungul peretelui cu biroul. X = 0 e în colțul cu peretele spre Dormitor 1, iar valorile cresc spre fereastra de colț.
- **Y** e înălțimea; Y = 0 e pardoseala.
- **Z** iese din perete spre aparatul foto; Z = 0 e fața peretelui.

`Camera.backproject(uv, "Z", 0)` transformă un pixel de pe perete în coordonate reale. Așa s-au estimat întrerupătorul, priza și plinta.

## Ce e diferit față de polițe

- **Fotografia e mică**, 311 × 554 px. Randarea se face la 6x și iese la 3x (933 × 1662 px), cu un blur ușor pe marginile pieselor noi, ca să se potrivească cu claritatea pozei.
- **Lumina.** Culoarea fiecărei fețe se calculează din albedo × balansul de alb al pozei × lumina peretelui din dreptul ei (`Scene` din `render.py`). Albedoul stejarului e citit pe imaginile BoConcept; peretele alb e referința. Din calcul sunt scoase biroul, fereastra, pata de soare și întrerupătorul.
- **Umbrele** cad pe perete (dedesubtul și lângă comodă) și pe pardoseală, cu ocluzie de contact la picioare (`Canvas.multiply_plane`).
- **Biroul din poză** stă în bufferul de adâncime (`Scene.occluders`), ca piesele noi să treacă în spatele lui unde e cazul.
