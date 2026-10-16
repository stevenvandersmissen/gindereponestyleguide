"""Verschuift de letter G in het zegel optisch naar links.

De G staat geometrisch perfect in het midden (bbox-midden 750.0 op een doek van
1500), maar haar massa ligt rechts van het midden: zwaartepunt x = 753.9. Daardoor
leest ze als "net niet gecentreerd". Dit script verplaatst alleen de G; de schijf,
de gouden ring, de haarlijn en de rode ruit blijven exact waar ze staan.

Methode: de G zit in een vak dat volledig binnen de effen zwarte schijf valt
(gemeten: RGB 11,10,9 zonder korrel of verloop binnen r < 676). Het vak wordt
uitgelezen, de oude plek wordt met diezelfde zwartwaarde gevuld en het vak wordt
N pixels naar links teruggezet met een max-blend, zodat de antialiasing van de
letterranden exact behouden blijft.

    python3 src/zegel.py <pixels>     # standaard 12
"""
import sys
import numpy as np
from PIL import Image

SRC = "00_brand/GINDER_zegel_1500.png"
BOX = (460, 420, 1040, 1170)      # ruim om de G heen, ver binnen de haarlijn
BLACK = (11, 10, 9)               # de grondkleur van de schijf, gemeten


def shift_g(path: str, n: int) -> Image.Image:
    """Geeft het zegel terug met de G n pixels naar links."""
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    x0, y0, x1, y1 = BOX
    patch = a[y0:y1, x0:x1].copy()

    # oude plek wissen met de grondkleur van de schijf
    a[y0:y1, x0:x1, 0] = BLACK[0]
    a[y0:y1, x0:x1, 1] = BLACK[1]
    a[y0:y1, x0:x1, 2] = BLACK[2]
    a[y0:y1, x0:x1, 3] = 255

    # verschoven terugzetten; de G is overal lichter dan de grond, dus max()
    # bewaart de letter inclusief haar zachte randen zonder dubbele randjes
    dst = a[y0:y1, x0 - n:x1 - n]
    np.maximum(dst, patch, out=dst)
    return Image.fromarray(a)


def centroid(im: Image.Image) -> float:
    """Zwaartepunt van de gouden letter, in x."""
    a = np.array(im.convert("RGBA")).astype(int)
    rgb, al = a[..., :3], a[..., 3]
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    inner = np.hypot(xx - (w - 1) / 2, yy - (h - 1) / 2) < 640
    g = inner & (yy > 400) & (al > 200) & (rgb[..., 0] > 110) & (rgb[..., 0] > rgb[..., 2] + 35)
    return float(np.where(g)[1].mean())


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    out = shift_g(SRC, n)
    out.save(SRC)
    print(f"G {n} px naar links · zwaartepunt {centroid(out):.1f} (doekmidden 749.5)")
