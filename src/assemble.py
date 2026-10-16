"""Bouwt GINDER_stijlgids.html: template + ingesloten fonts, beelden en logotype."""
import base64, os, re
from PIL import Image

t = open("src/template.html").read()

# ---------- logotype-varianten op webmaat ----------
os.makedirs("src/web", exist_ok=True)
master = Image.open("00_brand/GINDER_logotype_kleur.png").convert("RGBA")
zegel = Image.open("00_brand/GINDER_zegel_1500.png").convert("RGBA")

def rs(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)

def mono(src, rgb, w):
    s = rs(src, w)
    img = Image.new("RGBA", s.size, rgb + (0,)); img.putalpha(s.split()[3]); return img

rs(master, 1000).save("src/web/l_colour.webp", "WEBP", quality=84, method=6)
mono(master, (192, 138, 59), 900).save("src/web/l_gold.webp", "WEBP", quality=88, method=6)
mono(master, (212, 186, 150), 700).save("src/web/l_bone.webp", "WEBP", quality=88, method=6)
mono(master, (11, 10, 9), 700).save("src/web/l_black.webp", "WEBP", quality=88, method=6)
rs(zegel, 420).save("src/web/l_zegel.webp", "WEBP", quality=88, method=6)

def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode()

# ---------- fonts ----------
for tok, p in [("__F_PIRATA__", "pirata"), ("__F_ARCHIVO__", "archivoblack"), ("__F_INTER4__", "inter400"),
               ("__F_INTER6__", "inter600"), ("__F_MONO4__", "mono400"), ("__F_MONO7__", "mono700")]:
    t = t.replace(tok, b64(f"src/fonts/{p}.woff2"))

# ---------- beelden: alleen wat in de template voorkomt ----------
used = sorted(set(re.findall(r'class="im i-([a-z0-9-]+)"', t)))
vars_, rules = [], []
for cls in used:
    f = f"src/img/{cls.replace('-', '_')}.jpg"
    w, h = Image.open(f).size
    vars_.append(f"  --i-{cls}:url(data:image/jpeg;base64,{b64(f)});")
    rules.append(f".i-{cls}{{background-image:var(--i-{cls});aspect-ratio:{w}/{h}}}")

LOGOS = {"colour": ("l_colour.webp", "1673/434"), "gold": ("l_gold.webp", "1673/434"),
         "bone": ("l_bone.webp", "1673/434"), "black": ("l_black.webp", "1673/434"),
         "zegel": ("l_zegel.webp", "1/1")}
for cls, (f, ar) in LOGOS.items():
    vars_.append(f"  --l-{cls}:url(data:image/webp;base64,{b64('src/web/' + f)});")
    rules.append(f".l-{cls}{{background-image:var(--l-{cls});aspect-ratio:{ar}}}")

t = t.replace("__IMGVARS__", "\n".join(vars_))
t = t.replace("__IMGCSS__", "\n".join(rules))

# ---------- spikes ----------
sp, x, i = [], 0, 0
while x < 1200:
    sp.append(f"M{x} 0H{x+25}L{x+12.5:.1f} {28 if i % 2 == 0 else 17}Z"); x += 25; i += 1
t = t.replace("__SPIKEROW__", f'<path d="{" ".join(sp)}"/>')

left = sorted(set(re.findall(r"__[A-Z0-9_]+__", t)))
if left:
    print("!! openstaande tokens:", left)

open("GINDER_stijlgids.html", "w").write(t)
print("beelden:", ", ".join(used))
print(f"GINDER_stijlgids.html — {os.path.getsize('GINDER_stijlgids.html')/1024:.0f} KB")
