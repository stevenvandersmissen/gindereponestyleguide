"""Bouwt de logotype-kit voor Spotify, Instagram en Facebook.

Bron: de vier logotypes in 00_brand/ (kleur, goud, bot, zwart), raster 1673 x 434.
Er wordt nergens opgeschaald — elk vlak gebruikt het logotype kleiner dan de master.

Twee mappen:

  platform/     kant-en-klare vlakken. Grond = doekkorrel uit het artwork zelf,
                verschoven naar bone, blush of ash; plus een donkere variant met
                het gouden logotype. Logotype binnen de veilige zone van het vlak.
  transparant/  de vier versies los, per platform op maat, met alfakanaal.

    python3 src/logokit.py
"""
import os
import numpy as np
from PIL import Image

import ground as G

OUT = "00_brand/logotype_kit"
MASTER = {k: f"00_brand/GINDER_logotype_{k}.png" for k in ("kleur", "goud", "bot", "zwart")}
GRAIN_SRC, GRAIN_BOX = "uploads/gobeklitepePriest_MASTER.png", (60, 120, 700, 760)

GRONDEN = {                    # naam: (kleur, welke logotypeversie erop hoort)
    "bone":  ((212, 186, 150), "kleur"),
    "blush": ((221, 139, 114), "zwart"),
    "ash":   ((189, 169, 151), "zwart"),
    "zwart": ((11, 10, 9),     "goud"),
}

# vlak: (breedte, hoogte, logotypebreedte, verticale verschuiving, kwaliteit, maxKB)
VLAKKEN = {
    "spotify-header":   (2660, 1140, 900, -0.06, 92, None),   # naam van Spotify komt linksonder → logo iets hoger
    "spotify-playlist": (640,  640,  430,  0.00, 92, 4000),
    "ig-post":          (1080, 1350, 740,  0.00, 92, None),
    "ig-story":         (1080, 1920, 760, -0.02, 92, None),   # binnen de veilige 1080 x 1330
    "fb-omslag":        (851,  315,  520,  0.00, 88, 100),    # Facebook eist < 100 KB
    "fb-ogimage":       (1200, 630,  720,  0.00, 92, None),
}

BREEDTES = {"spotify": 820, "instagram": 1080, "facebook": 560}


def srgb():
    try:
        from PIL import ImageCms
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


def korrel(w, h, rgb, seed=11):
    """Doekkorrel uit het artwork, verschoven naar de gevraagde grondkleur."""
    patch = Image.open(GRAIN_SRC).convert("RGB").crop(GRAIN_BOX)
    tex = G.tile_texture(patch, w, h, seed=seed)
    a = np.asarray(tex).astype(np.float32)
    a += np.array(rgb, np.float32) - a.reshape(-1, 3).mean(0)
    if sum(rgb) < 120:                       # donkere grond: korrel indikken i.p.v. clippen
        m = a.reshape(-1, 3).mean(0)
        a = m + (a - m) * 0.35
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def plaats(canvas, logo, breedte, dy):
    w = breedte
    h = round(logo.height * w / logo.width)
    lg = logo.resize((w, h), Image.LANCZOS)
    x = (canvas.width - w) // 2
    y = round((canvas.height - h) / 2 + dy * canvas.height)
    canvas.paste(lg, (x, y), lg)
    return canvas


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
    os.makedirs(f"{OUT}/platform", exist_ok=True)
    os.makedirs(f"{OUT}/transparant", exist_ok=True)
    icc = srgb()
    logos = {k: Image.open(v).convert("RGBA") for k, v in MASTER.items()}

    for vlak, (w, h, lw, dy, q, maxkb) in VLAKKEN.items():
        for i, (gnaam, (rgb, versie)) in enumerate(GRONDEN.items()):
            canvas = korrel(w, h, rgb, seed=11 + i * 7).convert("RGBA")
            canvas = plaats(canvas, logos[versie], lw, dy).convert("RGB")
            p = f"{OUT}/platform/GINDER_evergreen_{vlak}-logotype-{gnaam}_{w}x{h}_v01.jpg"
            qq, kb = opslaan(canvas, p, q, maxkb, icc)
            print(f"{os.path.basename(p):<62} {kb:7.1f} KB  q{qq}")

    for plat, bw in BREEDTES.items():
        for versie, logo in logos.items():
            h = round(logo.height * bw / logo.width)
            p = f"{OUT}/transparant/GINDER_evergreen_logotype-{versie}-{plat}_{bw}x{h}_v01.png"
            logo.resize((bw, h), Image.LANCZOS).save(p, "PNG", optimize=True)
            print(f"{os.path.basename(p):<62} {os.path.getsize(p)/1024:7.1f} KB")
