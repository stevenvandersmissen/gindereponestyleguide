"""Alle platformformaten uit het single-artwork van de titeltrack (stormLady).

Dit artwork raakt alle vier de randen: de bliksems snijden de bovenrand, het
gewaad en de halftoon bloeden door de onderrand, de hoorns komen tot vlak bij
de zijkanten. Het mag dus niet verlengd en niet bijgesneden worden. Elk vlak
dat niet vierkant is, krijgt daarom de paneelmethode: het hele doek staat als
paneel op een grondvlak dat uit het beeld zelf komt — dezelfde papierkorrel,
de gemiddelde grondkleur van het doek. De band ernaast of eronder is het
altaar: daar hoort tekst, nergens anders.

Bron is 1254 x 1254. Er wordt nergens opgeschaald, dus dat is meteen de
bovengrens: de 1:1 komt op 1254 en niet op de 3000 die Spotify vraagt.

    python3 src/stormkit.py
"""
import os
import numpy as np
from PIL import Image

import ground as G

SRC = "uploads/stormLady_MASTER.png"
OUT = "00_brand/storm_kit"
PATCH = (20, 860, 260, 1100)      # 240 px, 99,99 % zuiver en zonder vouwlijn — tegelt naadloos

# (map, naam, W, H, paneelbreedte, x, y, kwaliteit, maxKB)
#   paneelbreedte = breedte van het doek in het vlak; "c" = gecentreerd
VLAKKEN = [
    # ── vierkant: het doek zelf, alleen verkleind ────────────────────────────
    ("1_vierkant", "cover",            1254, 1254, 1254, "c", "c", 95, None),
    ("1_vierkant", "vierkant",         1080, 1080, 1080, "c", "c", 94, None),
    ("1_vierkant", "vierkant-klein",    640,  640,  640, "c", "c", 94, None),
    ("1_vierkant", "thumbnail",         320,  320,  320, "c", "c", 94, None),
    # ── Spotify ──────────────────────────────────────────────────────────────
    ("2_spotify",  "header",           2660, 1140, 1000, "c", "c", 92, None),
    ("2_spotify",  "canvas",           1080, 1920, 1080, "c", 300, 93, None),
    ("2_spotify",  "galerij",          2048, 1152, 1010, "c", "c", 92, None),
    ("2_spotify",  "playlist",          640,  640,  640, "c", "c", 94, 4000),
    ("2_spotify",  "playlist-klein",    300,  300,  300, "c", "c", 94, 4000),
    # ── Instagram ────────────────────────────────────────────────────────────
    ("3_instagram", "post-4x5",        1080, 1350, 1080, "c",  80, 93, None),
    ("3_instagram", "post-vierkant",   1080, 1080, 1080, "c", "c", 94, None),
    ("3_instagram", "gridtegel-3x4",   1080, 1440, 1080, "c",  80, 93, None),
    ("3_instagram", "story-reel",      1080, 1920, 1080, "c", 300, 93, None),
    # ── Facebook ─────────────────────────────────────────────────────────────
    ("4_facebook",  "omslag",           851,  315,  275, "c", "c", 90, 100),
    ("4_facebook",  "eventomslag",     1920, 1005,  885, "c", "c", 92, None),
    ("4_facebook",  "groepsomslag",    1640,  856,  736, "c", "c", 92, None),
    ("4_facebook",  "ogimage",         1200,  630,  550, "c", "c", 92, None),
    ("4_facebook",  "post-vierkant",   1080, 1080, 1080, "c", "c", 94, None),
    ("4_facebook",  "post-4x5",        1080, 1350, 1080, "c",  80, 93, None),
    ("4_facebook",  "story",           1080, 1920, 1080, "c", 300, 93, None),
]


def srgb():
    try:
        from PIL import ImageCms
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


def vlak(art, W, H, pw, x, y, seed=5):
    """Paneel `art` op een grondvlak van W x H uit de korrel van het doek zelf."""
    ph = round(art.height * pw / art.width)
    panel = art.resize((pw, ph), Image.LANCZOS) if pw != art.width else art
    if W == pw and H == ph:
        return panel.copy()
    grond = G.tile_texture(art.crop(PATCH), W, H, seed=seed)
    a = np.asarray(grond).astype(np.float32)
    a = np.clip(a + (G.clean_mean(art) - a.reshape(-1, 3).mean(0)), 0, 255).astype(np.uint8)
    out = Image.fromarray(a)
    px = (W - pw) // 2 if x == "c" else int(x)
    py = (H - ph) // 2 if y == "c" else int(y)
    out.paste(panel, (px, py))
    return out


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
    print("bron:", art.size, "· grondkleur", G.clean_mean(art).round(1))
    cache = {}
    totaal = 0
    for i, (mapnaam, naam, W, H, pw, x, y, q, maxkb) in enumerate(VLAKKEN):
        os.makedirs(f"{OUT}/{mapnaam}", exist_ok=True)
        sleutel = (W, H, pw, x, y)
        im = cache.get(sleutel) or vlak(art, W, H, pw, x, y, seed=5 + i * 3)
        cache[sleutel] = im
        p = f"{OUT}/{mapnaam}/GINDER_gospel_storm-{naam}_{W}x{H}_v01.jpg"
        qq, kb = opslaan(im, p, q, maxkb, icc)
        totaal += kb
        print(f"{mapnaam}/{os.path.basename(p):<56} {kb:7.1f} KB  q{qq}")

    # lossless versie van de cover: sommige distributeurs vragen PNG
    p = f"{OUT}/1_vierkant/GINDER_gospel_storm-cover_1254x1254_v01.png"
    art.save(p, "PNG", optimize=True, **({"icc_profile": icc} if icc else {}))
    print(f"1_vierkant/{os.path.basename(p):<56} {os.path.getsize(p)/1024:7.1f} KB  PNG")
    print(f"totaal {totaal/1024:.1f} MB in {len(VLAKKEN)+1} bestanden")
