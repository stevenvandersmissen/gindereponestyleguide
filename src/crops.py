"""Rendert de vaste crops voor de vier artworks, in releasevolgorde.

  1  storm     single + titeltrack   she_brought_the_storm.jpeg  (1254², paneelmethode)
  2  gobekli   single                gobeklitepePriest_MASTER.png (3000²)
  3  blood     single                bloodMeridian_MASTER.png     (3000 × 4008)
  -  epcover   de EP zelf            original_gospel.png          (4096²)

Regels uit de stijlgids:
 - nooit door een oog, hoorn of tand snijden
 - verticaler kader = de grond van het beeld zelf doorzetten (zelfde korrel,
   willekeurig gespiegelde tegels, verzachte naad); figuur nooit uitrekken
 - raakt het figuur alle vier de randen, dan verleng je niet en snij je niet:
   het doek wordt een paneel op de grondkleur (storm)
"""
from PIL import Image, ImageFilter
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ground as G

OUT = "02_crops"; HI = f"{OUT}/hires"
os.makedirs(HI, exist_ok=True)

def inset(box, im, n=28):
    x0, y0, x1, y1 = box
    return (x0 + n if x0 == 0 else x0, y0 + n if y0 == 0 else y0,
            x1 - n if x1 >= im.width - 1 else x1, y1 - n if y1 >= im.height - 1 else y1)

def save(im, name, w, h, q=92):
    r = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.1, 52, 3))
    path = (HI if max(w, h) > 2000 and w != 3000 else OUT) + f"/GINDER_gospel_crop-{name}_{w}x{h}_v01.jpg"
    r.convert("RGB").save(path, "JPEG", quality=q, optimize=True, subsampling=0)
    print(f"  {os.path.basename(path):52s} {os.path.getsize(path)/1024:7.0f} KB")

def pair(im, name, w, h):
    save(im, name, w, h); save(im, name, w * 2, h * 2)

# ========================================================= 1 — STORM (single + titeltrack)
# Bliksems raken de bovenrand, het gewaad de onderrand, de hoorns bijna de zijkanten.
# Verlengen kan dus niet en croppen snijdt door de hoorns -> paneel op de grondkleur.
# Bron is 1254² : geen 2160-varianten, dat zou opschalen zijn.
s = Image.open("uploads/stormLady_MASTER.png").convert("RGB")
SP = (20, 860, 260, 1100)                            # 240 px zuiver doek, zonder vouwlijn
print("1 — We brought the storm inside and called it gospel (single)   monster", SP)
save(s, "storm-1x1", 1254, 1254)
save(s, "storm-1x1", 1080, 1080)
save(G.panel(s, 4/5,   60, SP, seed=51), "storm-4x5",  1080, 1350)
save(G.panel(s, 3/4,   80, SP, seed=52), "storm-3x4",  1080, 1440)
save(G.panel(s, 9/16, 300, SP, seed=53), "storm-9x16", 1080, 1920)

# ========================================================= 2 — GÖBEKLI TEPE
# Figuur start pas op rij 70: boven de hoorns ligt schone blush.
g = Image.open("uploads/gobeklitepePriest_MASTER.png").convert("RGB")
GB = inset(G.largest_clean_rect(g), g)
print("2 — Göbekli Tepe   monster", GB)
save(g, "gobekli-1x1", 3000, 3000); save(g, "gobekli-1x1", 1080, 1080)
pair(G.extend(g, GB, top=750,  fade=260, seed=11), "gobekli-4x5",  1080, 1350)
pair(G.extend(g, GB, top=1000, fade=260, seed=12), "gobekli-3x4",  1080, 1440)
pair(G.extend(g, GB, top=2333, fade=300, seed=13), "gobekli-9x16", 1080, 1920)

# ========================================================= 3 — BLOOD MERIDIAN
# 3:4 is bijna het origineel. 1:1 van bovenaf (voeten mogen weg, tong niet).
# 9:16 = as bijzetten boven het hoofd; onderaan niets, anders zweven de voeten.
b = Image.open("uploads/bloodMeridian_MASTER.png").convert("RGB")
BB = inset(G.largest_clean_rect(b), b)
print("3 — Blood Meridian   monster", BB)
save(b.crop((0, 0, 3000, 3000)), "blood-1x1", 3000, 3000)
save(b.crop((0, 0, 3000, 3000)), "blood-1x1", 1080, 1080)
pair(b.crop((0, 0, 3000, 3750)), "blood-4x5", 1080, 1350)
pair(b.crop((0, 0, 3000, 4000)), "blood-3x4", 1080, 1440)
pair(G.extend(b, BB, top=1325, fade=300, seed=31), "blood-9x16", 1080, 1920)

# ========================================================= EP-COVER
# Bliksems raken de bovenrand -> boven nooit verlengen. Onderaan rotspuin: dat groeit mee.
# 9:16 = strakke uitsnede op het figuur; het logotype valt weg, dat hoort niet op een Canvas.
e = Image.open("uploads/original_gospel.png").convert("RGB")
RUB = (2800, 3450, 4090, 4060)
print("EP-cover   monster", RUB)
save(e, "epcover-1x1", 3000, 3000); save(e, "epcover-1x1", 1080, 1080)
pair(G.extend(e, RUB, bottom=1024, fade=280, seed=21), "epcover-4x5", 1080, 1350)
pair(G.extend(e, RUB, bottom=1365, fade=300, seed=22), "epcover-3x4", 1080, 1440)
x = round(4096 * 0.115); w916 = round(4096 * 9 / 16)
pair(e.crop((x, 0, x + w916, 4096)), "epcover-9x16", 1080, 1920)

print("\nklaar:", len([f for f in os.listdir(OUT) if f.endswith('.jpg')]), "in", OUT,
      "+", len(os.listdir(HI)), "in", HI)
