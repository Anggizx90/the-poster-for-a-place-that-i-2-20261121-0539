#!/usr/bin/env python3
"""VELMORA — a travel poster for a place that isn't there.

A program that draws one travel poster (1024x1024 PNG) with Pillow and
writes it to /output/entry.png (or ./entry.png when /output is absent).

The place: VELMORA, a crater lake high in the northern ranges that holds
the sky — on still nights the aurora pools in the water so deeply that
glass-sailed skiffs seem to drift across the stars themselves.

Everything is drawn with code: gradient sky, aurora ribbons, stars, moon,
mountain ridge, lake with reflections, glass-sailed skiffs with lanterns,
pine shore, and the place name set in Noto Serif Display Black.

Deterministic: fixed seed, no timestamps, no network, no input files.
Re-running produces byte-identical output.
"""

import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- constants

W, H = 1024, 1024          # final poster size
SS = 2                     # supersample factor (render at 2048, downscale)
TITLE_FONT = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"

# Palette — deep indigo night, emerald aurora, warm lantern amber, cream type
SKY_TOP = (10, 14, 42)
SKY_MID = (16, 42, 66)
SKY_HORIZON = (38, 92, 96)
HORIZON_GLOW = (214, 164, 96)      # warm amber glow behind the ridge
AURORA = [(125, 255, 176), (61, 220, 151), (86, 232, 205), (168, 255, 200)]
RIDGE = (8, 16, 34)
LAKE_TOP = (14, 44, 62)
LAKE_BOTTOM = (6, 14, 30)
CREAM = (245, 234, 210)
BORDER = (238, 226, 198)
LANTERN = (255, 190, 90)

SEED = 20261121


# ---------------------------------------------------------------- helpers

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(w, h, stops):
    """stops: list of (position 0..1, rgb). Returns an RGB image."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = lerp(c0, c1, f)
                break
        else:
            col = stops[-1][1]
        for x in range(w):
            px[x, y] = col
    return img


def sine_band_points(x0, x1, y_base, amp, freq, phase, step=8):
    pts = []
    for x in range(x0, x1 + 1, step):
        y = y_base + amp * math.sin(freq * (x - x0) + phase)
        pts.append((x, y))
    return pts


def aurora_ribbon(layer, x0, x1, y_base, amp, freq, phase, thick, color, alpha):
    """One translucent wavy aurora band, drawn as a filled sine ribbon."""
    top = sine_band_points(x0, x1, y_base, amp, freq, phase)
    bottom = [(x, y + thick) for (x, y) in reversed(top)]
    d = ImageDraw.Draw(layer)
    d.polygon(top + bottom, fill=color + (alpha,))


def tracked_text(draw, cx, y, text, font, fill, tracking, shadow=None):
    """Draw text centred on cx, with manual letter-spacing (tracking in px)."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        if shadow is not None:
            draw.text((x + 2, y + 3), ch, font=font, fill=shadow)
        draw.text((x, y), ch, font=font, fill=fill)
        x += wch + tracking
    return total


# ---------------------------------------------------------------- scene

def draw_sky(base, rng, s):
    w, h = base.size
    sky = vertical_gradient(w, h, [
        (0.00, SKY_TOP),
        (0.45, SKY_MID),
        (0.62, SKY_HORIZON),
        (1.00, LAKE_BOTTOM),
    ])
    base.paste(sky, (0, 0))

    # warm glow hugging the horizon behind the ridge
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gy = int(h * 0.60)
    gd.ellipse([-w * 0.25, gy - int(h * 0.16), w * 1.25, gy + int(h * 0.10)],
               fill=HORIZON_GLOW + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(int(90 * s)))
    base.paste(Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB"), (0, 0))

    # stars — fewer, dimmer, kept clear of the title band
    stars = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(210):
        x = rng.randint(0, w - 1)
        y = rng.randint(int(h * 0.20), int(h * 0.55))
        r = rng.choice([1, 1, 1, 2, 2, 3]) * s
        a = rng.randint(60, 200)
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 235, a))
    base.paste(Image.alpha_composite(base.convert("RGBA"), stars).convert("RGB"), (0, 0))

    # moon with soft halo, upper LEFT — clear of the title
    moon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    mx, my, mr = int(w * 0.085), int(h * 0.13), int(26 * s)
    md.ellipse([mx - mr * 2, my - mr * 2, mx + mr * 2, my + mr * 2],
               fill=(235, 240, 255, 46))
    md.ellipse([mx - mr, my - mr, mx + mr, my + mr],
               fill=(240, 242, 250, 235))
    md.ellipse([mx - mr * 0.45, my - mr * 0.30, mx - mr * 0.10, my + mr * 0.05],
               fill=(214, 218, 232, 160))
    md.ellipse([mx + mr * 0.15, my + mr * 0.25, mx + mr * 0.45, my + mr * 0.55],
               fill=(214, 218, 232, 130))
    moon = moon.filter(ImageFilter.GaussianBlur(int(2 * s)))
    base.paste(Image.alpha_composite(base.convert("RGBA"), moon).convert("RGB"), (0, 0))

    # aurora — dramatic curtains: wide ribbons plus vertical ray streaks
    aur = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    aurora_ribbon(aur, -40, w + 40, int(h * 0.17), int(52 * s), 0.0016, 0.6,
                  int(170 * s), AURORA[1], 95)
    aurora_ribbon(aur, -40, w + 40, int(h * 0.28), int(66 * s), 0.0013, 2.1,
                  int(210 * s), AURORA[0], 130)
    aurora_ribbon(aur, -40, w + 40, int(h * 0.39), int(56 * s), 0.0018, 4.0,
                  int(150 * s), AURORA[2], 100)
    # one bright curtain fold on the right, to balance the moon on the left
    aurora_ribbon(aur, int(w * 0.52), w + 40, int(h * 0.26), int(58 * s), 0.0015, 1.2,
                  int(180 * s), AURORA[0], 110)
    # vertical rays hanging from the middle curtain
    ad = ImageDraw.Draw(aur)
    for i in range(60):
        x = rng.randint(int(w * 0.05), int(w * 0.95))
        y0 = int(h * 0.24) + rng.randint(-int(30 * s), int(60 * s))
        ln = rng.randint(int(90 * s), int(260 * s))
        wd = rng.randint(int(4 * s), int(16 * s))
        col = rng.choice(AURORA)
        ad.polygon([(x - wd, y0), (x + wd, y0),
                    (x + wd // 2, y0 + ln), (x - wd // 2, y0 + ln)],
                   fill=col + (rng.randint(40, 95),))
    aur = aur.filter(ImageFilter.GaussianBlur(int(18 * s)))
    # screen-blend the aurora over the sky so it glows instead of greying it
    base_rgb = base.convert("RGB")
    scr = ImageChops.screen(base_rgb, aur.convert("RGB"))
    mask = aur.split()[3].point(lambda a: int(a * 0.95))
    base.paste(scr, (0, 0), mask)
    return base


def ridge_points(w, h, rng, base_y, amp):
    pts = [(0, h)]
    x = 0
    y = base_y
    while x < w:
        step = rng.randint(int(50), int(150))
        x = min(x + step, w)
        y = base_y + rng.randint(-amp, amp)
        pts.append((x, y))
    pts.append((w, h))
    return pts


def peak_ridge(w, h, base_y, peaks, s):
    """A mountain skyline from explicit (x_fraction, peak_height_px) peaks."""
    pts = [(0, h), (0, base_y)]
    for xf, ph in peaks:
        pts.append((int(w * xf), base_y - int(ph * s)))
    pts.append((w, base_y))
    pts.append((w, h))
    return pts


def draw_ridge_and_lake(base, rng, s):
    w, h = base.size
    d = ImageDraw.Draw(base, "RGBA")
    horizon = int(h * 0.60)

    # far ridge — hazier blue, tall distinct peaks
    far_peaks = [(0.00, 26), (0.07, 78), (0.15, 34), (0.24, 104),
                 (0.36, 44), (0.48, 86), (0.60, 38), (0.71, 110),
                 (0.83, 48), (0.92, 70), (1.00, 30)]
    far = peak_ridge(w, h, horizon - int(10 * s), far_peaks, s)
    d.polygon(far, fill=(30, 56, 86, 255))
    # snow caps on the tallest far peaks
    snow = (205, 222, 236, 235)
    for xf, ph in [(0.24, 104), (0.71, 110), (0.48, 86)]:
        px, py = int(w * xf), horizon - int(10 * s) - int(ph * s)
        cap = int(26 * s)
        d.polygon([(px - cap, py + cap), (px, py), (px + cap, py + cap)],
                  fill=snow)
    # near ridge — darker, lower, in front
    near_peaks = [(0.00, 18), (0.12, 44), (0.28, 22), (0.44, 52),
                  (0.58, 26), (0.76, 46), (0.90, 24), (1.00, 34)]
    near = peak_ridge(w, h, horizon + int(8 * s), near_peaks, s)
    d.polygon(near, fill=RIDGE + (255,))

    # lake: mirror of the sky, darker, from the horizon down
    lake = vertical_gradient(w, h - horizon, [(0.0, LAKE_TOP), (1.0, LAKE_BOTTOM)])
    base.paste(lake, (0, horizon))

    # aurora reflections — broad soft vertical streaks in the lake
    refl = Image.new("RGBA", (w, h - horizon), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for _ in range(34):
        x = rng.randint(int(w * 0.05), int(w * 0.95))
        rw = rng.randint(int(10 * s), int(44 * s))
        rh = rng.randint(int(60 * s), int(260 * s))
        col = rng.choice(AURORA)
        rd.polygon([(x, 0), (x + rw, 0), (x + rw // 2, rh), (x - rw // 2, rh)],
                   fill=col + (rng.randint(45, 95),))
    refl = refl.filter(ImageFilter.GaussianBlur(int(12 * s)))
    # composite reflections only over the lake region
    tmp = base.convert("RGBA")
    tmp.paste(Image.alpha_composite(tmp.crop((0, horizon, w, h)),
                                    refl).convert("RGB"), (0, horizon))
    base.paste(tmp.convert("RGB"), (0, 0))

    # moon path on the water — one soft narrow band under the moon
    mp = Image.new("RGBA", (w, h - horizon), (0, 0, 0, 0))
    md = ImageDraw.Draw(mp)
    mx = int(w * 0.085)
    md.polygon([(mx - int(8 * s), 0), (mx + int(8 * s), 0),
                (mx + int(30 * s), h - horizon), (mx - int(30 * s), h - horizon)],
               fill=(235, 240, 255, 28))
    for i in range(10):
        y = i * int((h - horizon) / 10)
        ww = int((16 + i * 5) * s)
        md.rectangle([mx - ww // 2, y, mx + ww // 2, y + int(4 * s)],
                     fill=(235, 240, 255, 22))
    mp = mp.filter(ImageFilter.GaussianBlur(int(6 * s)))
    tmp = base.convert("RGBA")
    tmp.paste(Image.alpha_composite(tmp.crop((0, horizon, w, h)), mp).convert("RGB"),
              (0, horizon))
    base.paste(tmp.convert("RGB"), (0, 0))
    return base


def draw_pines(draw, x, base_y, height, color, rng, s):
    """A little pine silhouette (stacked triangles + trunk)."""
    wdt = height * 0.42
    tiers = 4
    for i in range(tiers):
        ty = base_y - height + i * (height / tiers) * 0.72
        th = height / tiers * 1.15
        tw = wdt * (0.45 + 0.55 * (i + 1) / tiers)
        draw.polygon([(x - tw / 2, ty + th), (x, ty), (x + tw / 2, ty + th)],
                     fill=color)
    draw.rectangle([x - 2 * s, base_y - height * 0.06, x + 2 * s, base_y],
                   fill=color)


def draw_shore(base, rng, s):
    w, h = base.size
    d = ImageDraw.Draw(base, "RGBA")
    shore_y = int(h * 0.90)
    # dark foreground shore, curving up at the edges to frame the lake
    d.polygon([(0, h), (0, shore_y + int(30 * s)),
               (int(w * 0.30), shore_y - int(6 * s)),
               (int(w * 0.70), shore_y - int(6 * s)),
               (w, shore_y + int(30 * s)), (w, h)],
              fill=(5, 10, 22, 255))
    # pine clusters on the left and right of the shore
    for cx, hh in [(0.05, 150), (0.12, 108), (0.19, 76),
                   (0.81, 76), (0.88, 112), (0.95, 152)]:
        draw_pines(d, int(w * cx), shore_y + int(38 * s),
                   int(hh * s), (4, 9, 20, 255), rng, s)
    # a small lit boathouse on the right shore — the promise of a warm stay
    bx, by = int(w * 0.70), shore_y + int(10 * s)
    bw2, bh2 = int(84 * s), int(52 * s)
    d.rectangle([bx, by - bh2, bx + bw2, by], fill=(12, 16, 30, 255))
    d.polygon([(bx - int(8 * s), by - bh2), (bx + bw2 // 2, by - bh2 - int(30 * s)),
               (bx + bw2 + int(8 * s), by - bh2)], fill=(8, 11, 22, 255))
    d.rectangle([bx + int(14 * s), by - int(30 * s), bx + int(32 * s), by - int(12 * s)],
                fill=(255, 196, 110, 255))
    d.rectangle([bx + int(50 * s), by - int(30 * s), bx + int(68 * s), by - int(12 * s)],
                fill=(255, 196, 110, 255))
    d.ellipse([bx + bw2 // 2 - int(5 * s), by - bh2 - int(44 * s),
               bx + bw2 // 2 + int(5 * s), by - bh2 - int(34 * s)],
              fill=LANTERN + (255,))
    return base


def draw_skiff(draw, x, y, scale, sail_color, rng, s):
    """A small glass-sailed skiff with a warm lantern, on the lake."""
    hull_w, hull_h = int(74 * scale * s), int(12 * scale * s)
    # hull
    draw.polygon([(x - hull_w // 2, y), (x + hull_w // 2, y),
                  (x + hull_w // 2 - int(10 * scale * s), y + hull_h),
                  (x - hull_w // 2 + int(10 * scale * s), y + hull_h)],
                 fill=(10, 14, 26, 255))
    # mast
    mast_h = int(64 * scale * s)
    draw.line([x, y, x, y - mast_h], fill=(16, 20, 34, 255), width=max(2, int(3 * scale * s)))
    # glass sail — translucent, catching the aurora
    sail = Image.new("RGBA", draw.im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sail)
    sd.polygon([(x, y - mast_h), (x + int(34 * scale * s), y - int(4 * scale * s)),
                (x, y - int(4 * scale * s))], fill=sail_color + (150,))
    sd.polygon([(x, y - mast_h), (x - int(26 * scale * s), y - int(4 * scale * s)),
                (x, y - int(4 * scale * s))], fill=sail_color + (105,))
    draw._image.paste(Image.alpha_composite(draw._image.convert("RGBA"), sail).convert("RGB"), (0, 0))
    # lantern on the bow + its reflection
    lx, ly = x + hull_w // 2 - int(8 * scale * s), y - int(6 * scale * s)
    draw.ellipse([lx - 4 * s, ly - 4 * s, lx + 4 * s, ly + 4 * s], fill=LANTERN + (255,))
    draw.ellipse([lx - 2 * s, ly + hull_h + 4 * s, lx + 2 * s, ly + hull_h + 16 * s],
                 fill=LANTERN + (90,))
    # soft reflection of the sail on the water below the hull
    refl = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rw = int(30 * scale * s)
    rd.polygon([(x - rw, y + hull_h), (x + rw, y + hull_h),
                (x + rw // 2, y + hull_h + int(46 * scale * s)),
                (x - rw // 2, y + hull_h + int(46 * scale * s))],
               fill=sail_color + (52,))
    refl = refl.filter(ImageFilter.GaussianBlur(int(6 * s)))
    draw._image.paste(Image.alpha_composite(draw._image.convert("RGBA"), refl).convert("RGB"), (0, 0))


def draw_title(base, s):
    w, h = base.size
    d = ImageDraw.Draw(base, "RGBA")
    size = int(118 * s)
    font = ImageFont.truetype(TITLE_FONT, size)
    # fit the name to the width
    while d.textlength("VELMORA", font=font) > w * 0.86 and size > 40:
        size -= 4
        font = ImageFont.truetype(TITLE_FONT, size)
    cy = int(h * 0.075)
    tracked_text(d, w // 2, cy, "VELMORA", font, CREAM,
                 tracking=int(14 * s), shadow=(6, 10, 26, 220))
    # thin rule + diamond under the name
    rule_y = cy + size + int(16 * s)
    rw = int(w * 0.30)
    d.line([w // 2 - rw, rule_y, w // 2 - int(14 * s), rule_y],
           fill=CREAM + (230,), width=max(2, int(3 * s)))
    d.line([w // 2 + int(14 * s), rule_y, w // 2 + rw, rule_y],
           fill=CREAM + (230,), width=max(2, int(3 * s)))
    d.polygon([(w // 2, rule_y - int(7 * s)), (w // 2 + int(7 * s), rule_y),
               (w // 2, rule_y + int(7 * s)), (w // 2 - int(7 * s), rule_y)],
              fill=CREAM + (230,))
    return base


def render():
    rng = random.Random(SEED)
    w, h = W * SS, H * SS
    img = Image.new("RGB", (w, h), SKY_TOP)
    img = draw_sky(img, rng, SS)
    img = draw_ridge_and_lake(img, rng, SS)
    d = ImageDraw.Draw(img, "RGBA")
    # skiffs on the lake — a large hero boat lower-left, a smaller one far right
    draw_skiff(d, int(w * 0.30), int(h * 0.76), 1.5, AURORA[0], rng, SS)
    draw_skiff(d, int(w * 0.70), int(h * 0.68), 0.62, AURORA[2], rng, SS)
    img = draw_shore(img, rng, SS)
    img = draw_title(img, SS)
    # poster border
    bd = ImageDraw.Draw(img, "RGBA")
    bw = int(14 * SS)
    bd.rectangle([bw // 2, bw // 2, w - bw // 2, h - bw // 2],
                 outline=BORDER + (255,), width=bw)
    return img.resize((W, H), Image.LANCZOS)


def main():
    out_dir = "/output" if os.path.isdir("/output") else "."
    out_path = os.path.join(out_dir, "entry.png")
    img = render()
    img.save(out_path, format="PNG", optimize=True)
    print(f"wrote {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
