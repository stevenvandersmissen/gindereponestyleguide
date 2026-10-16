"""Grondtextuur-gereedschap: schone stukken vinden en er doek mee bijmaken."""
from PIL import Image
import numpy as np, random

def ground_colour(im, frac=0.012):
    a = np.asarray(im); H, W, _ = a.shape; k = max(6, int(H * frac))
    edge = np.concatenate([a[:k].reshape(-1, 3), a[:, :k].reshape(-1, 3), a[:, -k:].reshape(-1, 3)])
    return np.median(edge, axis=0)

def largest_clean_rect(im, tol=40, scale=8, min_px=240, purity=0.998):
    """Grofweg het grootste zuivere grondvlak zoeken (rastersearch met integraalbeeld)."""
    small = im.resize((im.width // scale, im.height // scale), Image.BILINEAR)
    a = np.asarray(small).astype(float)
    m = (np.abs(a - ground_colour(im)).max(axis=2) < tol)
    H, W = m.shape
    ii = np.zeros((H + 1, W + 1)); ii[1:, 1:] = np.cumsum(np.cumsum(m.astype(float), 0), 1)
    best = None; step = max(1, W // 36)
    ys = list(range(0, H, step)) + [H]; xs = list(range(0, W, step)) + [W]
    for i, y0 in enumerate(ys[:-1]):
        for y1 in ys[i + 1:]:
            for j, x0 in enumerate(xs[:-1]):
                for x1 in xs[j + 1:]:
                    area = (x1 - x0) * (y1 - y0)
                    if best and area <= best[0]:
                        continue
                    s = ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
                    if s / area >= purity:
                        best = (area, x0, y0, x1, y1)
    if not best:
        return None
    _, x0, y0, x1, y1 = best
    box = (x0 * scale, y0 * scale, x1 * scale, y1 * scale)
    return box if min(box[2] - box[0], box[3] - box[1]) >= min_px else None

def _ramp(n):
    return np.linspace(0, 1, n, dtype=np.float32)

def tile_texture(patch, W, H, seed=7, overlap=0.22):
    """Vult W x H met `patch`: willekeurige spiegelingen, naden verzacht met alfaverlopen."""
    rnd = random.Random(seed)
    pw, ph = patch.size
    ox, oy = max(8, int(pw * overlap)), max(8, int(ph * overlap))
    CW, CH = W + 2 * pw, H + 2 * ph
    acc = np.zeros((CH, CW, 3), np.float32); wgt = np.zeros((CH, CW, 1), np.float32)
    bx, by = np.ones(pw, np.float32), np.ones(ph, np.float32)
    bx[:ox] = _ramp(ox); bx[-ox:] = _ramp(ox)[::-1]
    by[:oy] = _ramp(oy); by[-oy:] = _ramp(oy)[::-1]
    blend = (by[:, None] * bx[None, :])[:, :, None] + 1e-4
    y = 0
    while y < CH:
        x = 0
        while x < CW:
            p = patch
            if rnd.random() < .5: p = p.transpose(Image.FLIP_LEFT_RIGHT)
            if rnd.random() < .5: p = p.transpose(Image.FLIP_TOP_BOTTOM)
            a = np.asarray(p).astype(np.float32)
            y1, x1 = min(y + ph, CH), min(x + pw, CW)
            h, w = y1 - y, x1 - x
            acc[y:y1, x:x1] += a[:h, :w] * blend[:h, :w]
            wgt[y:y1, x:x1] += blend[:h, :w]
            x += pw - ox
        y += ph - oy
    out = (acc / wgt).clip(0, 255).astype(np.uint8)
    off_y, off_x = ph, pw
    return Image.fromarray(out[off_y:off_y + H, off_x:off_x + W])

def match_colour(fill, ref):
    """Trekt de gemiddelde kleur van `fill` gelijk met die van referentiestrook `ref`."""
    f = np.asarray(fill).astype(np.float32); r = np.asarray(ref).astype(np.float32)
    d = r.reshape(-1, 3).mean(0) - f.reshape(-1, 3).mean(0)
    return Image.fromarray(np.clip(f + d, 0, 255).astype(np.uint8))

def content_alpha(im, tol=45, edge=26, blur=4):
    """255 waar het beeld figuur is (geen grond). Houdt hoorns en voeten scherp in de naad;
    de verweerde doekrand zelf telt niet mee, die mag juist wegvloeien."""
    from PIL import ImageFilter
    a = np.asarray(im).astype(np.float32)
    c = (np.abs(a - ground_colour(im)).max(axis=2) > tol).astype(np.uint8) * 255
    c[:edge] = 0; c[-edge:] = 0; c[:, :edge] = 0; c[:, -edge:] = 0
    return np.asarray(Image.fromarray(c, "L").filter(ImageFilter.GaussianBlur(blur))).astype(np.float32)

def extend(im, patch_box, top=0, bottom=0, fade=220, seed=7):
    """Verlengt verticaal met doek dat uit `patch_box` van het beeld zelf komt."""
    W, H = im.size
    patch = im.crop(patch_box)
    out = Image.new("RGB", (W, H + top + bottom))
    if top:
        f = tile_texture(patch, W, top + fade, seed)
        f = match_colour(f, im.crop((0, 0, W, 60)))
        out.paste(f, (0, 0))
    if bottom:
        f = tile_texture(patch, W, bottom + fade, seed + 1)
        f = match_colour(f, im.crop((0, H - 60, W, H)))
        out.paste(f, (0, H + top - fade))
    m = np.full((H, W), 255, np.float32)
    if top:
        m[:fade] = _ramp(fade)[:, None] * 255
    if bottom:
        m[-fade:] = _ramp(fade)[::-1, None] * 255
    m = np.maximum(m, content_alpha(im))          # figuur blijft volledig dekkend
    out.paste(im, (0, top), Image.fromarray(m.clip(0, 255).astype(np.uint8), "L"))
    return out

def clean_mean(im, tol=40):
    """Gemiddelde kleur van alle zuivere grondpixels — betrouwbaarder dan de randmediaan."""
    a = np.asarray(im).astype(np.float32)
    return a[(np.abs(a - ground_colour(im)).max(axis=2) < tol)].mean(0)

def panel(im, ratio, top, patch_box, seed=5):
    """Zet het hele doek als paneel op een grondvlak uit het beeld zelf.
    Voor artwork dat alle vier de randen raakt: niet verlengen, niet snijden."""
    W = im.width; H = round(W / ratio)
    f = np.asarray(tile_texture(im.crop(patch_box), W, H, seed=seed)).astype(np.float32)
    f = np.clip(f + (clean_mean(im) - f.reshape(-1, 3).mean(0)), 0, 255).astype(np.uint8)
    out = Image.fromarray(f); out.paste(im, (0, top)); return out
