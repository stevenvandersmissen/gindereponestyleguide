"""Alle platformformaten uit de EP-cover (original_gospel, 4096 x 4096).

Dit doek laat meer toe dan het single-artwork. Het figuur staat volledig binnen
het kader, bovenaan ligt bone met bliksems, onderaan rotspuin dat meegroeit.
Daarom drie methodes in plaats van één:

  doek     vierkante vlakken: alleen verkleinen, verder niets.
  verleng  staande vlakken (4:5, 3:4): het puin onderaan groeit mee, het doek
           blijft ongemoeid. Boven nooit verlengen - de bliksems lopen de
           bovenrand uit en zouden halverwege het beeld doodvallen.
  band     liggende vlakken: een horizontale uitsnede over de volle breedte.
           Geen paneel: dat werd bleek en klein, de band is veel sterker.
  figuur   9:16: strakke uitsnede op het figuur (x 471, breedte 2304). Het
           logotype valt weg, en dat hoort ook: Spotify toont de naam zelf en
           verbiedt ingebrande tekst op een Canvas.

Elke band wordt gecontroleerd tegen de ankerpunten van het doek. De kop moet er
altijd volledig in; het logotype en de gouden stip mogen er alleen helemaal in
of helemaal buiten vallen. Een band die door letters snijdt, laat het script
niet door.

    python3 src/epkit.py
"""
import os
import numpy as np
from PIL import Image

import ground as G

SRC = "uploads/original_gospel.png"
OUT = "00_brand/epcover_kit"
RUB = (2800, 3450, 4090, 4060)    # rotspuin rechtsonder - tegelt naadloos, zelfde monster als crops.py
X916, W916 = 471, 2304            # 9:16 uitsnede op het figuur

# ankerpunten in het doek (y-bereik, gemeten op het 4096-raster)
KOP = (560, 1810)                 # hanenkam + snavel: moet altijd volledig in beeld
LOGO = (2030, 2300)               # "Ginder" in goud, rechts
STIP = (2590, 2870)               # gouden stip rechtsonder

# (map, naam, W, H, methode, parameter, kwaliteit, maxKB)
VLAKKEN = [
    # ── vierkant: het doek zelf, alleen verkleind ────────────────────────────
    ("1_vierkant",  "cover",           3000, 3000, "doek",    None, 95, 9000),
    ("1_vierkant",  "vierkant",        1080, 1080, "doek",    None, 94, None),
    ("1_vierkant",  "vierkant-klein",   640,  640, "doek",    None, 94, None),
    ("1_vierkant",  "thumbnail",        320,  320, "doek",    None, 94, None),
    # ── Spotify ──────────────────────────────────────────────────────────────
    ("2_spotify",   "header",          2660, 1140, "band",     250, 92, None),
    ("2_spotify",   "canvas",          1080, 1920, "figuur",  None, 93, None),
    ("2_spotify",   "galerij",         2048, 1152, "band",     270, 92, None),
    ("2_spotify",   "playlist",         640,  640, "doek",    None, 94, 4000),
    ("2_spotify",   "playlist-klein",   300,  300, "doek",    None, 94, 4000),
    # ── Instagram ────────────────────────────────────────────────────────────
    ("3_instagram", "post-4x5",        1080, 1350, "verleng", 1024, 93, None),
    ("3_instagram", "post-vierkant",   1080, 1080, "doek",    None, 94, None),
    ("3_instagram", "gridtegel-3x4",   1080, 1440, "verleng", 1365, 93, None),
    ("3_instagram", "story-reel",      1080, 1920, "figuur",  None, 93, None),
    # ── Facebook ─────────────────────────────────────────────────────────────
    ("4_facebook",  "omslag",           851,  315, "band",     480, 90, 100),
    ("4_facebook",  "eventomslag",     1920, 1005, "band",     400, 92, None),
    ("4_facebook",  "groepsomslag",    1640,  856, "band",     400, 92, None),
    ("4_facebook",  "ogimage",         1200,  630, "band",     400, 92, None),
    ("4_facebook",  "post-vierkant",   1080, 1080, "doek",    None, 94, None),
    ("4_facebook",  "post-4x5",        1080, 1350, "verleng", 1024, 93, None),
    ("4_facebook",  "story",           1080, 1920, "figuur",  None, 93, None),
]


def srgb():
    try:
        from PIL import ImageCms
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


def controleer(naam, y0, y1):
    """De kop helemaal in beeld; logotype en stip helemaal in of helemaal buiten."""
    a, b = KOP
    assert y0 <= a and b <= y1, f"{naam}: band {y0}-{y1} snijdt de kop ({a}-{b})"
    for sleutel, (a, b) in (("logotype", LOGO), ("stip", STIP)):
        if not (y0 <= a and b <= y1) and not (b < y0 or a > y1):
            raise AssertionError(f"{naam}: band {y0}-{y1} snijdt het {sleutel} ({a}-{b})")
    return "logotype" if y0 <= LOGO[0] and LOGO[1] <= y1 else "geen logotype"


def vlak(art, naam, W, H, methode, par, seed):
    if methode == "doek":
        return art.resize((W, H), Image.LANCZOS), "doek"
    if methode == "verleng":
        im = G.extend(art, RUB, bottom=par, fade=300, seed=seed)
        return im.resize((W, H), Image.LANCZOS), f"puin +{par}"
    if methode == "figuur":
        im = art.crop((X916, 0, X916 + W916, art.height))
        return im.resize((W, H), Image.LANCZOS), f"uitsnede x{X916}"
    if methode == "band":
        h = round(art.width * H / W)
        y0 = par
        assert y0 + h <= art.height, f"{naam}: band valt onder de doekrand"
        info = controleer(naam, y0, y0 + h)
        im = art.crop((0, y0, art.width, y0 + h))
        return im.resize((W, H), Image.LANCZOS), f"band y{y0}-{y0+h} · {info}"
    raise ValueError(methode)


def opslaan(im, path, q, max_kb, icc):
    kw = {"optimize": True, "subsampling": 0}
    if icc:
        kw["icc_profile"] = icc
    im.save(path, "JPEG", quality=q, **kw)
    while max_kb and os.path.getsize(path) / 1024 > max_kb and q > 40:
        q -= 4
        im.save(path, "JPEG", quality=q, **kw)
    return q, os.path.getsize(path) / 1024


if __name__ == "__main__":
    icc = srgb()
    art = Image.open(SRC).convert("RGB")
    assert art.size == (4096, 4096), art.size
    print("bron:", art.size, "· grondkleur", G.clean_mean(art).round(1))
    cache, totaal = {}, 0.0
    for i, (mapnaam, naam, W, H, methode, par, q, maxkb) in enumerate(VLAKKEN):
        os.makedirs(f"{OUT}/{mapnaam}", exist_ok=True)
        sleutel = (W, H, methode, par)
        if sleutel in cache:
            im, info = cache[sleutel]
        else:
            im, info = vlak(art, naam, W, H, methode, par, seed=7 + i * 3)
            cache[sleutel] = (im, info)
        p = f"{OUT}/{mapnaam}/GINDER_gospel_epcover-{naam}_{W}x{H}_v01.jpg"
        qq, kb = opslaan(im, p, q, maxkb, icc)
        totaal += kb
        print(f"{mapnaam:<12} {naam:<15} {W:>4}x{H:<4} {kb:8.1f} KB  q{qq}  {info}")

    # lossless versie van de cover: sommige distributeurs vragen PNG
    p = f"{OUT}/1_vierkant/GINDER_gospel_epcover-cover_3000x3000_v01.png"
    art.resize((3000, 3000), Image.LANCZOS).save(
        p, "PNG", optimize=True, **({"icc_profile": icc} if icc else {}))
    kb = os.path.getsize(p) / 1024
    totaal += kb
    print(f"{'1_vierkant':<12} {'cover (PNG)':<15} 3000x3000 {kb:8.1f} KB")
    print(f"\ntotaal {totaal/1024:.1f} MB in {len(VLAKKEN)+1} bestanden")
