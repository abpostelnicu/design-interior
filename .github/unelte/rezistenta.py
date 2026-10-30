"""Verificări simple de rezistență pentru piesele prinse în perete: tije filetate în consolă, smulgerea din
ancoră și greutăți din volume.

Sunt verificări de ordinul de mărime, fără coeficienți de siguranță. În plan și în README le însoțesc mereu fișa
ancorei chimice pentru peretele real și o probă de încărcare (de exemplu 1,5 × sarcina, 24 de ore).

Ipotezele, ca în proiectele „Polițe viniluri”:
- polița plină stă doar în tije, ca o consolă, cu sarcina în mijlocul adâncimii P (cm); momentul din dreptul
  peretelui se împarte egal la tije;
- secțiunea tijei e cea din fundul filetului (d3), deci W = π · d3³ / 32;
- când polița se sprijină pe perete la muchia de jos a spatelui, tija trage din ancoră cu M / (T/2) (T = grosimea
  poliței, cm; tija e la jumătatea ei).

    from unelte import rezistenta as rz
    kg = rz.kg_placa(120, 25, 3.6, "stejar") + 32            # polița și discurile de pe ea
    sigma, rezerva = rz.rod_check(kg, P=25, rods=3, fy=rz.FY["8.8"])
    kn = rz.rod_pull(kg, P=25, T=3.6, rods=3)
"""
import math

G = 9.81                                                   # m/s²
# diametrul la fundul filetului metric (mm): d3 = d − 1,22687 · pas
D3 = {"M6": 4.773, "M8": 6.466, "M10": 8.160, "M12": 9.853, "M16": 13.546}
# limita de curgere (MPa) a claselor de tije folosite până acum: 4.8 e tija zincată obișnuită
FY = {"4.8": 320.0, "8.8": 640.0}
# densități (g/cm³), estimate în proiectele de până acum
RHO = {"stejar": 0.72, "placaj": 0.68, "microciment": 1.8, "gfrc": 2.1}


def moment(kg, P):
    """Momentul (N·mm) din dreptul peretelui: kg încărcate în mijlocul adâncimii P (cm)."""
    return kg * G * P / 2 * 10.0


def modul(d3=D3["M12"]):
    """Modulul de rezistență al tijei (mm³), la fundul filetului."""
    return math.pi * d3 ** 3 / 32.0


def rod_check(kg, P, rods, fy=FY["4.8"], d3=D3["M12"]):
    """(σ în MPa, rotunjit; rezerva fy / σ, cu 2 zecimale) pentru tijele care țin singure polița plină."""
    sigma = moment(kg, P) / rods / modul(d3)
    return round(sigma), round(fy / sigma, 2)


def rod_pull(kg, P, T, rods):
    """Forța de smulgere pe tijă (kN, 2 zecimale) când polița se sprijină pe perete la muchia de jos.

    E sarcina pe care trebuie s-o țină ancora chimică din fiecare gaură, fără coeficienți de siguranță; o compari
    cu fișa ancorei pentru materialul peretelui (BCA, cărămidă plină sau cu goluri, beton).
    """
    return round(moment(kg, P) / (T / 2 * 10.0) / rods / 1000.0, 2)


def greutate(volum_cm3, material):
    """kg dintr-un volum (cm³) de material din RHO, sau cu densitatea dată ca număr (g/cm³)."""
    rho = RHO[material] if isinstance(material, str) else float(material)
    return volum_cm3 * rho / 1000.0


def kg_placa(L, P, T, material):
    """kg ai unei plăci pline de L × P × T cm."""
    return greutate(L * P * T, material)
