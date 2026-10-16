"""Bouwt het overzichtsblad van de vaste crops + de previews voor de stijlgids."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = "02_crops"
VOID, GOLD, BONE, DIM = (11, 10, 9), (192, 138, 59), (212, 186, 150), (120, 108, 92)
AB = lambda s: ImageFont.truetype("/tmp/archivoblack.ttf", s)
MO = lambda s: ImageFont.truetype("/tmp/mono700.ttf", s)

TRACKS = [("storm",   "1 — WE BROUGHT THE STORM INSIDE AND CALLED IT GOSPEL   ·   single + titeltrack"),
          ("gobekli", "2 — GÖBEKLI TEPE   ·   single"),
          ("blood",   "3 — BLOOD MERIDIAN   ·   single"),
          ("epcover", "EP-COVER   ·   we brought the storm inside and called it gospel")]
RATIOS = [("1x1_1080x1080", "1:1", "cover · feed · avatarbron"),
          ("4x5_1080x1350", "4:5", "IG- en FB-feed"),
          ("3x4_1080x1440", "3:4", "IG-grid · poster"),
          ("9x16_1080x1920", "9:16", "story · reel · canvas")]

def build(TH, pad, head, cap, title_h, path, q=88):
    cells = [[Image.open(f"{OUT}/GINDER_gospel_crop-{k}-{r}_v01.jpg") for r, _, _ in RATIOS]
             for k, _ in TRACKS]
    widths = [round(c.width * TH / c.height) for c in cells[0]]
    W = sum(widths) + pad * (len(widths) - 1) + pad * 4
    rowh = head + TH + cap + pad
    H = title_h + rowh * len(TRACKS) + pad * 2
    sheet = Image.new("RGB", (W, H), VOID)
    d = ImageDraw.Draw(sheet)
    x0 = pad * 2
    d.text((x0, pad * 1.4), "GINDER — VASTE CROPS", font=AB(round(TH * .062)), fill=BONE)
    d.text((x0, pad * 1.4 + TH * .085), "drie singles in releasevolgorde + de EP-cover  ·  "
           "één goedgekeurde uitsnede per ratio  ·  v01",
           font=MO(round(TH * .032)), fill=DIM)
    y = title_h
    for (key, label), row in zip(TRACKS, cells):
        d.text((x0, y + head * .18), label, font=AB(round(TH * .045)), fill=GOLD)
        x = x0
        for im, w, (rk, rlab, use) in zip(row, widths, RATIOS):
            sheet.paste(im.resize((w, TH), Image.LANCZOS), (x, y + head))
            yy = y + head + TH + cap * .22
            d.text((x, yy), rlab, font=AB(round(TH * .034)), fill=BONE)
            d.text((x + TH * .085, yy + TH * .004), use, font=MO(round(TH * .026)), fill=DIM)
            d.text((x, yy + TH * .055), rk.split("_")[1].replace("x", " × ") + " px",
                   font=MO(round(TH * .024)), fill=(90, 80, 68))
            x += w + pad
        y += rowh
    sheet.save(path, "JPEG", quality=q, optimize=True)
    print(f"  {path}  {sheet.size[0]} × {sheet.size[1]}  {os.path.getsize(path)/1024:.0f} KB")
    return sheet

build(560, 26, 78, 62, 150, f"{OUT}/GINDER_crops_overzicht.jpg")          # levering
build(300, 15, 44, 36, 86, "src/img/crops_overzicht.jpg", q=74)           # in de gids

for r, tag in [("1x1_1080x1080", "11"), ("4x5_1080x1350", "45"), ("9x16_1080x1920", "916")]:
    im = Image.open(f"{OUT}/GINDER_gospel_crop-gobekli-{r}_v01.jpg")
    w = 440; im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
        f"src/img/crop_gobekli_{tag}.jpg", "JPEG", quality=76, optimize=True)
    print(f"  src/img/crop_gobekli_{tag}.jpg  {os.path.getsize(f'src/img/crop_gobekli_{tag}.jpg')/1024:.0f} KB")

im = Image.open(f"{OUT}/GINDER_gospel_crop-storm-9x16_1080x1920_v01.jpg")
w = 440; im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
    "src/img/crop_storm_916.jpg", "JPEG", quality=76, optimize=True)
print(f"  src/img/crop_storm_916.jpg  {os.path.getsize('src/img/crop_storm_916.jpg')/1024:.0f} KB")
