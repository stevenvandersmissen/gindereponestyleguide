"""Controleblad voor een platformkit: alle vlakken op schaal, met bijschrift.

    pip install brotli          # eenmalig per sessie, voor de woff2-fonts
    python3 src/kitblad.py 00_brand/epcover_kit "EP-cover"

Legt de bestanden per map op rijen, breekt af op de bladbreedte en zet onder
elk vlak de naam en de maat. Rood bijschrift = waarschuwing uit WAARSCHUWING.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, M, CEL = 1060, 28, 196          # bladbreedte, marge, maximale thumbhoogte
BONE, INKT, ROOD, GOUD = (233, 226, 212), (24, 22, 20), (176, 42, 36), (150, 110, 40)
KOPJES = {"1_vierkant": "vierkant — het doek zelf",
          "2_spotify": "Spotify", "3_instagram": "Instagram", "4_facebook": "Facebook"}
WAARSCHUWING = {}                   # bestandsnaam-deel -> rode regel


def ttf(naam, px):
    """woff2 uit src/fonts omzetten naar ttf in /tmp en laden."""
    uit = f"/tmp/{naam}.ttf"
    if not os.path.exists(uit):
        from fontTools.ttLib import TTFont
        f = TTFont(f"src/fonts/{naam}.woff2")
        f.flavor = None
        f.save(uit)
    return ImageFont.truetype(uit, px)


def blad(kit, titel, ondertitel=""):
    kop = ttf("archivoblack", 30)
    sub = ttf("mono400", 13)
    nm = ttf("inter600", 13)
    mt = ttf("mono400", 12)

    mappen = sorted(d for d in os.listdir(kit) if os.path.isdir(f"{kit}/{d}"))
    plan, y = [], M + 46 + (20 if ondertitel else 0)
    for d in mappen:
        plan.append(("kop", KOPJES.get(d, d), y)); y += 30
        x, rij = M, 0
        for f in sorted(os.listdir(f"{kit}/{d}")):
            if not f.lower().endswith((".jpg", ".png")):
                continue
            im = Image.open(f"{kit}/{d}/{f}")
            h = min(CEL, im.height); w = round(im.width * h / im.height)
            if w > 300:
                w = 300; h = round(im.height * w / im.width)
            naam = f.split("epcover-")[-1].split("storm-")[-1].rsplit("_", 2)[0]
            if f.lower().endswith(".png"):
                naam += " (png)"
            maat = f"{im.width}x{im.height}"
            breed = max(w, round(max(nm.getlength(naam), mt.getlength(maat))))
            if x + breed > W - M:
                y += rij + 46; x, rij = M, 0
            plan.append(("vlak", (f"{kit}/{d}/{f}", naam, maat, w, h, x, y), None))
            x += breed + 18; rij = max(rij, h)
        y += rij + 52

    s = Image.new("RGB", (W, y + 10), BONE)
    d = ImageDraw.Draw(s)
    d.text((M, M), titel, font=kop, fill=INKT)
    if ondertitel:
        d.text((M, M + 38), ondertitel, font=sub, fill=GOUD)
    for soort, data, yy in plan:
        if soort == "kop":
            d.text((M, yy), data.upper(), font=ttf("inter600", 15), fill=ROOD)
            d.line([(M, yy + 21), (W - M, yy + 21)], fill=(205, 196, 180), width=1)
            continue
        pad, naam, maat, w, h, x, yy = data
        im = Image.open(pad).convert("RGB").resize((w, h), Image.LANCZOS)
        s.paste(im, (x, yy))
        d.rectangle([x, yy, x + w - 1, yy + h - 1], outline=(190, 180, 164), width=1)
        d.text((x, yy + h + 6), naam, font=nm, fill=INKT)
        kleur = INKT
        for sleutel, regel in WAARSCHUWING.items():
            if sleutel in naam:
                maat, kleur = regel, ROOD
        d.text((x, yy + h + 22), maat, font=mt, fill=kleur)
    return s


if __name__ == "__main__":
    kit = sys.argv[1]
    titel = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(kit)
    onder = sys.argv[3] if len(sys.argv) > 3 else ""
    naam = sys.argv[4] if len(sys.argv) > 4 else f"{kit}/GINDER_{os.path.basename(kit)}_voorbeeld.png"
    s = blad(kit, titel, onder)
    s.save(naam)
    print(naam, s.size)
