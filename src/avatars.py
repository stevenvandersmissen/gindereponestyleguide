"""Maakt profielafbeeldingen van het zegel voor Spotify, Instagram en Facebook.

Waarom niet gewoon het zegel uploaden:

1. Het master-zegel is een transparante PNG. Facebook en Instagram zetten
   transparantie om naar een eigen achtergrond (meestal wit) — dat geeft een
   witte rand rond de schijf. Hier wordt daarom plat gezet op de eigen
   grondkleur (#0B0A09).
2. Alle drie de platformen tonen de avatar in een cirkel die exact even groot
   is als het vierkant. De gouden ring raakt in de master bijna de rand en kan
   door die masker-antialiasing net worden weggesneden. De schijf wordt daarom
   op 94 % gezet, met zwart eromheen: de ring blijft altijd heel.
3. Elk platform schaalt zelf naar een piepklein formaat. Beter één keer netjes
   met Lanczos verkleinen dan het aan hun encoder overlaten.

    python3 src/avatars.py
"""
import os
from PIL import Image

SRC = "00_brand/GINDER_zegel_1500.png"
OUT = "00_brand/avatars"
VOID = (11, 10, 9)
DISC = 0.94          # schijf t.o.v. de zijde — 6 % veiligheidsmarge voor de ronde uitsnede

# platform: (zijde, bestandsnaam, waarom dit formaat)
TARGETS = {
    "spotify":   (1500, "Spotify for Artists vraagt minstens 750 px; 1500 is de marge voor retina"),
    "instagram": (1080, "Instagram bewaart 320 px, toont ~110 px — groter aanleveren geeft de beste verkleining"),
    "facebook":  (1080, "Facebook toont 176 px desktop en 196 px mobiel, bewaart 320 px"),
}


def srgb():
    """sRGB-profiel om in te sluiten, als littlecms beschikbaar is."""
    try:
        from PIL import ImageCms
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


def build(side: int) -> Image.Image:
    seal = Image.open(SRC).convert("RGBA")
    d = round(side * DISC)
    if d % 2 != side % 2:        # even/oneven gelijk houden → exact centreren
        d -= 1
    canvas = Image.new("RGB", (side, side), VOID)
    small = seal.resize((d, d), Image.LANCZOS)
    off = (side - d) // 2
    canvas.paste(small, (off, off), small)
    return canvas


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icc = srgb()
    print("sRGB-profiel ingesloten:", bool(icc))
    for name, (side, _why) in TARGETS.items():
        im = build(side)
        p = f"{OUT}/GINDER_evergreen_avatar-zegel-{name}_{side}x{side}_v01.jpg"
        im.save(p, "JPEG", quality=95, subsampling=0, optimize=True,
                **({"icc_profile": icc} if icc else {}))
        print(f"{os.path.basename(p):<58} {os.path.getsize(p)/1024:6.1f} KB")

    # platte PNG voor wie lossless wil (Spotify accepteert PNG, Bandcamp ook)
    p = f"{OUT}/GINDER_evergreen_avatar-zegel_1500x1500_v01.png"
    build(1500).save(p, "PNG", optimize=True, **({"icc_profile": icc} if icc else {}))
    print(f"{os.path.basename(p):<58} {os.path.getsize(p)/1024:6.1f} KB")
