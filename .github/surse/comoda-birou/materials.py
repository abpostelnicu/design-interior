"""Materialele comodei: furnirul de stejar (natur și închis), riflajul fronturilor și oțelul negru al picioarelor.

Culorile vin din imaginile producătorului (BoConcept Element), aduse la lumina din fotografie prin peretele alb:
culoarea unei fețe = albedo × balansul de alb al pozei × lumina peretelui din dreptul ei.
"""
import cv2
import numpy as np

R_TEX = 12.0   # pixeli de textură pe cm

# albedo în sRGB (B, G, R), 0..1, citit pe fețele luminate din imaginile producătorului
ALBEDO = {
    "stejar": np.array([0.47, 0.61, 0.75], np.float32),         # natural oak veneer
    "stejar_inchis": np.array([0.215, 0.255, 0.31], np.float32),  # dark oak veneer
}
STEEL = np.array([0.085, 0.085, 0.09], np.float32)               # picioarele, negru mat


def veneer(w_cm, h_cm, rng, vertical=True, contrast=1.0):
    """Hartă de detaliu (media 1) pentru furnir de stejar tăiat radial: fibră dreaptă, cu dungi fine și raze."""
    w, h = int(w_cm * R_TEX) + 2, int(h_cm * R_TEX) + 2
    L, Wd = (h, w) if vertical else (w, h)          # L = de-a lungul fibrei
    cols = np.arange(Wd, dtype=np.float32)
    prof = np.ones(Wd, np.float32)
    for _ in range(max(int(Wd / R_TEX * 1.4), 1)):
        c, wd, a = rng.uniform(0, Wd), rng.uniform(0.6, 2.6), rng.uniform(0.02, 0.10)
        prof -= a * np.exp(-((cols - c) / wd) ** 2)
    band = cv2.GaussianBlur(rng.rand(1, Wd).astype(np.float32), (0, 0), sigmaX=R_TEX * 2.5)[0]
    prof *= 1 + 0.10 * (band - band.mean()) / max(band.std(), 1e-6) * 0.5
    rows = np.arange(L, dtype=np.float32)[:, None]
    wave = 1.2 * np.sin(rows / rng.uniform(300, 800) * 2 * np.pi + rng.uniform(0, 6.3))
    u = np.clip(cols[None, :] + wave, 0, Wd - 1).astype(np.float32)
    g = cv2.remap(prof[None, :].repeat(L, 0), u, np.repeat(rows, Wd, 1).astype(np.float32), cv2.INTER_LINEAR)
    # razele medulare, scurte și deschise la culoare, specifice stejarului
    fl = (rng.rand(L, Wd) < 0.0009).astype(np.float32)
    fl = cv2.GaussianBlur(cv2.resize(fl, (Wd, L)), (0, 0), sigmaX=0.6, sigmaY=R_TEX * 0.7)
    g = g * (1 + 2.2 * fl)
    g = 1 + (g / g.mean() - 1) * contrast
    tex = g if vertical else g.T
    return np.clip(tex, 0.7, 1.3).astype(np.float32)


def reeding(u_cm, pitch, side_light=0.06):
    """Umbrirea riflajului vertical: baghete convexe, cu rost întunecat între ele; lumina vine puțin din dreapta."""
    fr = np.mod(u_cm / pitch, 1.0)
    x = 2 * fr - 1
    nz = np.sqrt(np.clip(1 - 0.85 * x * x, 0, 1))
    f = 0.70 + 0.30 * nz + side_light * x
    groove = np.clip((np.abs(x) - 0.86) / 0.14, 0, 1)
    return f * (1 - 0.40 * groove)


def sample(tex, u_px, v_px):
    """Eșantionare biliniară cu repetare în oglindă; u = coloana, v = rândul."""
    h, w = tex.shape[:2]
    u = np.abs(np.mod(u_px, 2 * (w - 1)) - (w - 1))
    v = np.abs(np.mod(v_px, 2 * (h - 1)) - (h - 1))
    return cv2.remap(tex, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REFLECT)
