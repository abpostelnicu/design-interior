# Sursele variantelor C și D din „Comodă birou”: bufetele Cioata

Scripturile din acest folder generează randările, imaginea de comparație și planul tehnic ale variantelor C și D din [`Comoda birou/`](../../../../Comoda%20birou/README.md#variantele-c-și-d-de-la-cioata):
- **C:** bufetul Cioata Raya 116 (RA340), stejar Natural Oak, cu uși din lamele verticale și un mâner negru;
- **D:** bufetul Cioata Veneto 116 (VE340), același corp, cu uși din microciment C9 și un mâner rotund din stejar.

Amândouă au sertarul opțional VE390, în spatele ușilor. Variantele A și B, cu sursele lor din folderul de deasupra, rămân cum sunt.

Scripturile folosesc fotografia calibrată, camera, lumina și ocluderul biroului din proiect (`../camera.json`, `../core.py`, `../render.py`, `../materials.py`, `../design.py`). Din trusa comună [`.github/unelte/`](../../../unelte/README.md) vin microcimentul (`materiale.concrete_panel`), ușile (`usi.analizeaza` și `usi.deseneaza`), imaginea de comparație (`comparatie.compune`) și planul (`plan`). Biroul, priza și întrerupătorul din plan vin din `../drawing.py`, ca să fie desenate la fel ca la A și B.

Ce au general scripturile de aici a intrat în trusă: fronturile din lamele (`materiale.lamele`, `lamela_la` și `lamele_umbrire`, din `lamele` și `door_raya`), legenda ușilor cu nume și obstacol (`usi.deseneaza`, din `vedere_plan`) și umbrele unei piese pe picioare (`randare.umbre_pe_picioare`, din `shadows`). Testele din [`teste/test_unelte_cioata.py`](../../../unelte/teste/test_unelte_cioata.py) le compară cu aceste funcții, așa că, dacă le schimbi, rulezi și testele trusei. Un proiect nou pornește de la trusă.

## Fișiere

| Fișier | Rol |
|---|---|
| `varianta.py` | Sursa unică pentru C și D: corpul comun (`BUF`, din desenul cotat Cioata; ce e măsurat pe fotografiile producătorului e marcat `# est.`), sertarul VE390 (`SERTAR`), așezarea (centrat în peretele liber: `X0`, `X1`, `GAP_DESK`, `GAP_CORNER`), variantele cu prețurile și linkurile (`VARIANTE`), lamelele ușilor Raya (`lamele`, aceleași în randare și în plan) și verificarea ușilor (`doors`) |
| `randeaza.py` | Randează C și D în fotografie, plus `out/acum.jpg`: blatul și rama de stejar, banda neagră de sub blat, ușile (lamele cu rosturi și mânerul negru la C; microciment cu mânerul rotund la D), traversa și picioarele, cu umbre pe perete și pe pardoseală |
| `compara.py` | Imaginea cu trei panouri, Acum, C și D, la aceeași mărime ca a variantelor A și B |
| `planul.py` | Planul tehnic A3: vederea frontală cu C și planul cu ușile deschise și sertarul scos, la 1:15; secțiunea prin bufet și fața lui D, la 1:15; planul camerei la 1:50; notele |

## Cum regenerezi imaginile

Cu mediul Python al proiectului, din folderul de deasupra (vezi [README-ul lui](../README.md#cum-regenerezi-imaginile)):

```sh
cd ".github/surse/comoda-birou/cioata"
../.venv/bin/python varianta.py    # cotele, ușile la 90° și la 110°, prețurile
../.venv/bin/python randeaza.py    # out/propunere_C_cioata_raya.jpg, out/varianta_D_cioata_veneto.jpg și out/acum.jpg
../.venv/bin/python compara.py     # out/comparatie_acum_vs_propuneri_cioata.jpg (după randeaza.py)
../.venv/bin/python planul.py      # out/plan_tehnic_comoda_birou_cioata.pdf și .png
../.venv/bin/python ../../../unelte/plan.py verifica planul.py   # textele planului: 0 probleme
cp out/propunere_C_cioata_raya.jpg out/varianta_D_cioata_veneto.jpg out/comparatie_acum_vs_propuneri_cioata.jpg \
   out/plan_tehnic_comoda_birou_cioata.pdf out/plan_tehnic_comoda_birou_cioata.png "../../../../Comoda birou/"
```

Coordonatele sunt ale proiectului: X de-a lungul peretelui cu biroul, de la colț; Y în sus, de la pardoseală; Z din perete spre cameră, în cm.

## Cum sunt făcute

- **Corpul.** Cotele vin din desenul cotat Cioata: 116 × 48 × 82 cm, corpul de 62 cm de la 20 cm în sus, uși de 55 × 55 cm, traversa dintre picioare de la 14 la 20 cm. Grosimile (2,2 cm), picioarele (Ø ~2,4 cm, cu axul la ~12,5 cm de laterale și la ~5 cm de față și de spate) și mânerele (banda neagră de ~6 cm la Raya, discul de ~28 cm la Veneto) sunt măsurate pe fotografiile de produs, raportate la lățimea de 116 cm.
- **Culorile.** Albedourile sunt citite pe fotografiile de studio Cioata, raportate la fundalul lor alb, ca la stejarul BoConcept: stejarul Natural Oak, negrul mânerului, microcimentul C9 și stejarul mai deschis al mânerului rotund. Stejarul Cioata e masiv, cu fibra mai vizibilă decât furnirul, de aceea textura are contrast mai mare (parametrul `contrast` al lui `veneer`, între 1,7 și 2).
- **Ce se vede.** Aparatul foto e în stânga bufetului și deasupra lui, deci se văd doar fața și blatul. Marginea din stânga a fotografiei e la ~30 cm de colț, așa că bufetul apare de la ~29 cm încolo; banda neagră și mânerul rotund intră în cadru.
- **Rosturile.** În spatele ușilor e o față neagră, cât tot corpul: privirea piezișă prin rostul dintre ușă și lateral o atinge și nu mai ajunge la peretele din spate.
- **Umbrele.** Sub corpul adânc de 48 cm, pe perete și pe pardoseală, umbra e mai densă decât la comoda A/B: lumina intră doar prin fanta de 20 cm de sub corp. Picioarele au ocluzie de contact.
- **Ușile.** `usi.analizeaza` le socotește ca uși aplicate pe față, cu balamaua pe muchia exterioară a lateralului: la 90° ies în lateral cu grosimea lor, 2,2 cm. E cazul cel mai strâns; ușile Cioata stau în ramă și au ceva mai mult loc. Cu ~5,1 cm pe fiecare parte, amândouă ajung la 90°; cea din stânga atinge peretele la ~93°, cea din dreapta blatul la ~97,5°, doar când blatul e sub ~77 cm.

## De ce nu Atlas

Seria Atlas are corpuri cu sertare la vedere, dar nu și o compoziție de ~100–118 cm: nișa Atlas se prinde doar între două module, comoda cu 2 sertare are 70 cm, iar rollbox-ul are 50 × 48 × 63 cm, cu altă înălțime. Comodele Galla și Linea, cu 6 sertare, au 136 și 130 cm; se pot cere pe măsură, cu prețul la cerere. De aceea C și D sunt bufete cu uși, iar sertarul e cel opțional, VE390, din spatele ușilor.
