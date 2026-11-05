"""Stubbs Asphalt explainer: what happens when a crack goes unfixed.
Every frame drawn with pycairo, piped to ffmpeg.  Usage:
  python3 render.py                 -> out/stubbs_explainer.mp4
  python3 render.py still 12.5 30   -> out/still_12.5.png ... (preview frames)
"""
import math, os, random, subprocess, sys
from multiprocessing import Pool
import cairo

W, H, FPS = 1920, 1080, 30
DUR = 106.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- geometry
X0, X1 = 140, 1340          # diagram left/right
CX = 720                     # crack location
SKY = 250
L_SURF, L_BIND, L_BASE, L_SUB, L_BOT = 470, 530, 610, 770, 960
DW = X1 - X0

WATER = (0.25, 0.66, 0.96)
ICE = (0.84, 0.95, 1.0)
WARN = (0.90, 0.27, 0.23)

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)

def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3

def window(t, a, b, fi=0.5, fo=0.5):
    """1 inside [a,b] with fades."""
    return ease(prog(t, a, a + fi)) * (1 - ease(prog(t, b - fo, b)))

def gauss(x, s):
    return math.exp(-(x * x) / (2 * s * s))

def font(ctx, size, weight="black"):
    fam = {"black": "Inter Black", "bold": "Inter", "reg": "Inter"}[weight]
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL if weight == "reg" else cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)

def chrome(ctx, y0, y1, a=1.0):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0.0, 1, 1, 1, a)
    g.add_color_stop_rgba(0.45, 0.86, 0.86, 0.87, a)
    g.add_color_stop_rgba(0.55, 0.62, 0.62, 0.64, a)
    g.add_color_stop_rgba(1.0, 0.95, 0.95, 0.96, a)
    return g

def spaced_extent(ctx, text, sp):
    w = 0
    for ch in text:
        w += ctx.text_extents(ch).x_advance + sp
    return w - sp

def draw_text(ctx, text, x, y, size, weight="black", rgba=(1, 1, 1, 1), align="left",
              sp=0.0, chrome_fill=False):
    font(ctx, size, weight)
    tw = spaced_extent(ctx, text, sp) if sp else ctx.text_extents(text).x_advance
    if align == "center":
        x -= tw / 2
    elif align == "right":
        x -= tw
    if chrome_fill:
        ctx.set_source(chrome(ctx, y - size * 0.78, y + size * 0.05, rgba[3]))
    else:
        ctx.set_source_rgba(*rgba)
    if sp:
        cx = x
        for ch in text:
            ctx.move_to(cx, y)
            ctx.text_path(ch)
            cx += ctx.text_extents(ch).x_advance + sp
        ctx.fill()
    else:
        ctx.move_to(x, y)
        ctx.show_text(text)
    ctx.new_path()
    return tw

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

# ---------------------------------------------------------------- textures
def make_textures():
    rnd = random.Random(7)
    tex = {}

    def surf(h):
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, DW, h)
        return s, cairo.Context(s)

    # surface asphalt: fine aggregate
    s, c = surf(L_BIND - L_SURF)
    c.set_source_rgb(0.17, 0.17, 0.18); c.paint()
    for _ in range(4200):
        v = rnd.uniform(0.25, 0.5)
        c.set_source_rgba(v, v, v * 1.02, rnd.uniform(0.4, 0.9))
        c.arc(rnd.uniform(0, DW), rnd.uniform(0, s.get_height()), rnd.uniform(0.8, 2.4), 0, 6.3); c.fill()
    g = cairo.LinearGradient(0, 0, 0, 10)
    g.add_color_stop_rgba(0, 0.55, 0.55, 0.57, 0.9); g.add_color_stop_rgba(1, 0.2, 0.2, 0.2, 0)
    c.set_source(g); c.rectangle(0, 0, DW, 10); c.fill()
    tex["surf"] = s

    # binder: coarser aggregate
    s, c = surf(L_BASE - L_BIND)
    c.set_source_rgb(0.12, 0.12, 0.13); c.paint()
    for _ in range(1500):
        v = rnd.uniform(0.22, 0.45)
        r = rnd.uniform(2, 6)
        x, y = rnd.uniform(0, DW), rnd.uniform(0, s.get_height())
        c.set_source_rgba(v, v * 0.98, v * 0.95, 0.9)
        poly(c, x, y, r, rnd); c.fill()
    tex["bind"] = s

    # base rock: crushed stone
    s, c = surf(L_SUB - L_BASE)
    c.set_source_rgb(0.33, 0.30, 0.27); c.paint()
    for _ in range(2600):
        v = rnd.uniform(0.38, 0.68)
        r = rnd.uniform(4, 13)
        x, y = rnd.uniform(-10, DW + 10), rnd.uniform(-5, s.get_height() + 5)
        c.set_source_rgb(v, v * 0.95, v * 0.88)
        poly(c, x, y, r, rnd); c.fill_preserve()
        c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(1); c.stroke()
    tex["base"] = s

    # sub-base: compacted soil
    s, c = surf(L_BOT - L_SUB)
    g = cairo.LinearGradient(0, 0, 0, s.get_height())
    g.add_color_stop_rgb(0, 0.42, 0.31, 0.21); g.add_color_stop_rgb(1, 0.30, 0.21, 0.14)
    c.set_source(g); c.paint()
    for _ in range(3500):
        v = rnd.uniform(-0.08, 0.1)
        c.set_source_rgba(0.42 + v, 0.31 + v, 0.21 + v, 0.8)
        c.arc(rnd.uniform(0, DW), rnd.uniform(0, s.get_height()), rnd.uniform(1, 3), 0, 6.3); c.fill()
    for _ in range(120):
        v = rnd.uniform(0.35, 0.5)
        c.set_source_rgb(v, v * 0.9, v * 0.8)
        poly(c, rnd.uniform(0, DW), rnd.uniform(0, s.get_height()), rnd.uniform(3, 7), rnd); c.fill()
    tex["sub"] = s
    return tex

def poly(c, x, y, r, rnd):
    n = rnd.randint(5, 7)
    a0 = rnd.uniform(0, 6.3)
    for i in range(n):
        a = a0 + i * 2 * math.pi / n + rnd.uniform(-0.3, 0.3)
        rr = r * rnd.uniform(0.7, 1.15)
        px, py = x + rr * math.cos(a), y + rr * math.sin(a) * 0.8
        (c.move_to if i == 0 else c.line_to)(px, py)
    c.close_path()

TEX = None
LOGO = None

def crack_points(seed, depth_total, spread):
    rnd = random.Random(seed)
    pts = []
    x = 0.0
    for i in range(0, depth_total + 1, 8):
        pts.append((x, i))
        x += rnd.uniform(-spread, spread)
        x *= 0.85
    return pts

MAIN_CRACK = crack_points(3, L_BASE - L_SURF, 5)

def alligator_cracks():
    rnd = random.Random(11)
    out = []
    for i in range(16):
        x = CX + rnd.uniform(-330, 330)
        if abs(x - CX) < 25:
            continue
        depth = rnd.uniform(25, L_BASE - L_SURF - 10)
        out.append((x, crack_points(100 + i, int(depth), 4), abs(x - CX)))
    return sorted(out, key=lambda c: c[2])

ALLIGATOR = alligator_cracks()

# ---------------------------------------------------------------- state
def heave_profile(x, st):
    return st["sink"] * gauss(x - CX, 230) - st["heave"] * gauss(x - CX, 120)

def layer_offset(x, st, f):
    return heave_profile(x, st) * f

# ---------------------------------------------------------------- diagram
def draw_layer(ctx, key, y_top, f, st, build):
    if build <= 0:
        return
    s = TEX[key]
    h = s.get_height()
    ctx.save()
    ctx.rectangle(X0, SKY, DW, L_BOT - SKY); ctx.clip()
    slide = (1 - eout(build)) * 40
    if st["sink"] == 0 and st["heave"] == 0:
        ctx.set_source_surface(s, X0, y_top - slide)
        ctx.paint_with_alpha(ease(build))
    else:
        step = 6
        for xs in range(0, DW, step):
            d = layer_offset(X0 + xs + step / 2, st, f)
            ctx.save()
            ctx.rectangle(X0 + xs, y_top + d - slide - 2, step + 0.5, h + 2)
            ctx.clip()
            ctx.set_source_surface(s, X0, y_top + d - slide)
            ctx.paint_with_alpha(ease(build))
            ctx.restore()
    ctx.restore()

def crack_path(ctx, pts, cx, top, depth, w, st, f=1.0):
    pts = [(cx + px, top + py) for px, py in pts if py <= depth] or [(cx, top)]
    if depth > 0 and pts[-1][1] < top + depth:
        pts.append((pts[-1][0], top + depth))
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        k = 1 - 0.75 * (i / max(1, n - 1))
        d = layer_offset(x, st, f)
        left.append((x - w * k / 2, y + d))
        right.append((x + w * k / 2, y + d))
    ctx.move_to(*left[0])
    for p in left[1:]:
        ctx.line_to(*p)
    for p in reversed(right):
        ctx.line_to(*p)
    ctx.close_path()

def draw_section(ctx, st, t):
    a = st["diag"]
    if a <= 0:
        return
    ctx.push_group()
    # layers bottom-up
    draw_layer(ctx, "sub", L_SUB, 0.55, st, st["b_sub"])
    # mud overlay in sub-base
    if st["mud"] > 0:
        ctx.save(); ctx.rectangle(X0, L_SUB, DW, L_BOT - L_SUB); ctx.clip()
        g = cairo.RadialGradient(CX, L_SUB + 40, 20, CX, L_SUB + 40, 520)
        g.add_color_stop_rgba(0, 0.16, 0.11, 0.07, 0.85 * st["mud"])
        g.add_color_stop_rgba(0.7, 0.18, 0.13, 0.09, 0.5 * st["mud"])
        g.add_color_stop_rgba(1, 0.2, 0.14, 0.1, 0)
        ctx.set_source(g); ctx.paint()
        ctx.set_line_width(2)
        for i in range(7):
            yy = L_SUB + 25 + i * 24
            ctx.set_source_rgba(*WATER, 0.35 * st["mud"] * (1 - i / 9))
            for xs in range(-360, 361, 6):
                x = CX + xs
                y = yy + 5 * math.sin(xs / 30 + t * 2 + i) + layer_offset(x, st, 0.55)
                (ctx.move_to if xs == -360 else ctx.line_to)(x, y)
            ctx.stroke()
        ctx.restore()
    draw_layer(ctx, "base", L_BASE, 0.85, st, st["b_base"])
    # water soaking base
    if st["wet"] > 0:
        ctx.save(); ctx.rectangle(X0, L_BASE, DW, L_SUB - L_BASE + 4); ctx.clip()
        R = 60 + 520 * st["wet"]
        g = cairo.RadialGradient(CX, L_BASE + 10, 10, CX, L_BASE + 10, R)
        col = tuple(WATER[i] * (1 - st["ice"]) + ICE[i] * st["ice"] for i in range(3))
        g.add_color_stop_rgba(0, *col, 0.62)
        g.add_color_stop_rgba(0.75, *col, 0.42)
        g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g)
        ctx.scale(1, 1)
        ctx.paint_with_alpha(min(1, st["wet"] * 2.5))
        if st["ice"] > 0.05:
            rnd = random.Random(5)
            ctx.set_line_width(1.6)
            for _ in range(70):
                x = CX + rnd.uniform(-R * 0.8, R * 0.8)
                y = rnd.uniform(L_BASE + 8, L_SUB - 8) + layer_offset(x, st, 0.85)
                s = rnd.uniform(4, 8) * st["ice"]
                ctx.set_source_rgba(1, 1, 1, 0.8 * st["ice"] * clamp(1 - abs(x - CX) / R))
                for k in range(3):
                    ang = k * math.pi / 3
                    ctx.move_to(x - s * math.cos(ang), y - s * math.sin(ang))
                    ctx.line_to(x + s * math.cos(ang), y + s * math.sin(ang))
                ctx.stroke()
        ctx.restore()
    # voids
    if st["voids"] > 0:
        rnd = random.Random(9)
        for i in range(9):
            x = CX + rnd.uniform(-170, 170)
            y = rnd.uniform(L_BASE + 25, L_SUB - 25) + layer_offset(x, st, 0.85)
            k = clamp(st["voids"] * 1.4 - i * 0.07)
            if k <= 0:
                continue
            rx, ry = rnd.uniform(18, 42) * k, rnd.uniform(9, 18) * k
            ctx.save(); ctx.translate(x, y); ctx.scale(rx, ry)
            g = cairo.RadialGradient(0, 0, 0.2, 0, 0, 1)
            g.add_color_stop_rgba(0, 0.03, 0.03, 0.04, 0.95)
            g.add_color_stop_rgba(0.8, 0.05, 0.05, 0.06, 0.85)
            g.add_color_stop_rgba(1, 0.05, 0.05, 0.06, 0)
            ctx.set_source(g); ctx.arc(0, 0, 1, 0, 6.3); ctx.fill(); ctx.restore()
    # fines pumping up
    if st["pump"] > 0:
        rnd = random.Random(21)
        for i in range(60):
            x = CX + rnd.uniform(-260, 260)
            ph = (t * 0.35 + rnd.random()) % 1
            y = L_SUB + 40 - ph * 150 + layer_offset(x, st, 0.7)
            ctx.set_source_rgba(0.52, 0.38, 0.25, st["pump"] * math.sin(ph * math.pi))
            ctx.arc(x, y, rnd.uniform(2, 4), 0, 6.3); ctx.fill()
    draw_layer(ctx, "bind", L_BIND, 1.0, st, st["b_bind"])
    draw_layer(ctx, "surf", L_SURF, 1.0, st, st["b_surf"])

    # alligator cracks
    if st["gator"] > 0:
        n = len(ALLIGATOR)
        for i, (x, pts, dist) in enumerate(ALLIGATOR):
            k = clamp(st["gator"] * n * 0.9 - i)
            if k <= 0:
                continue
            ctx.set_source_rgb(0.02, 0.02, 0.02)
            crack_path(ctx, pts, x, L_SURF, pts[-1][1] * k, 4, st)
            ctx.fill()
    # main crack
    if st["crack"] > 0:
        depth = st["crack"]
        ctx.set_source_rgb(0.02, 0.02, 0.02)
        crack_path(ctx, MAIN_CRACK, CX, L_SURF, depth, st["cw"], st)
        ctx.fill()
        if st["water"] > 0:
            wd = min(depth, st["water"])
            col = tuple(WATER[i] * (1 - st["ice"]) + ICE[i] * st["ice"] for i in range(3))
            ctx.set_source_rgba(*col, 0.95)
            crack_path(ctx, MAIN_CRACK, CX, L_SURF, wd, st["cw"] * 0.8, st)
            ctx.fill()
        if st["fill"] > 0:
            fd = depth * st["fill"]
            ctx.set_source_rgb(0.05, 0.05, 0.06)
            crack_path(ctx, MAIN_CRACK, CX, L_SURF, fd, st["cw"] + 2, st)
            ctx.fill()
            # overband
            ob = eout(prog(st["fill"], 0.6, 1))
            if ob > 0:
                ctx.set_source_rgb(0.06, 0.06, 0.07)
                rrect(ctx, CX - 34 * ob, L_SURF - 4, 68 * ob, 9, 4); ctx.fill()
                ctx.set_source_rgba(1, 1, 1, 0.35)
                ctx.rectangle(CX - 30 * ob, L_SURF - 3, 60 * ob, 2); ctx.fill()
    # pothole
    if st["pothole"] > 0:
        p = eout(st["pothole"])
        hw, hd = 150 * p, 95 * p
        ctx.set_source_rgb(0.04, 0.04, 0.045)
        rnd = random.Random(4)
        ctx.move_to(CX - hw, L_SURF - 4 + layer_offset(CX - hw, st, 1))
        for i in range(0, 21):
            u = i / 20
            x = CX - hw + 2 * hw * u
            y = L_SURF + layer_offset(x, st, 1) + hd * math.sin(u * math.pi) ** 0.7 + rnd.uniform(-5, 5)
            ctx.line_to(x, y)
        ctx.line_to(CX + hw, L_SURF - 4 + layer_offset(CX + hw, st, 1))
        ctx.close_path(); ctx.fill()
        # rubble + puddle
        ctx.set_source_rgba(*WATER, 0.55 * p)
        ctx.save(); ctx.translate(CX, L_SURF + hd * 0.78 + layer_offset(CX, st, 1)); ctx.scale(hw * 0.55, 10 * p)
        ctx.arc(0, 0, 1, 0, 6.3); ctx.fill(); ctx.restore()
        for i in range(14):
            x = CX + rnd.uniform(-hw * 0.8, hw * 0.8)
            y = L_SURF + layer_offset(x, st, 1) + hd * 0.8 * math.sin((x - CX + hw) / (2 * hw + 1) * math.pi) ** 0.7
            v = rnd.uniform(0.2, 0.35)
            ctx.set_source_rgb(v, v, v)
            poly(ctx, x, y - 4, rnd.uniform(4, 9) * p, rnd); ctx.fill()
    # excavation (full replacement panel)
    if st.get("excavate", 0) > 0:
        e = st["excavate"]
        ctx.save()
        ctx.set_source_rgb(0.03, 0.03, 0.035)
        ctx.rectangle(CX - 380, L_SURF - 2, 760, (L_BOT - 60 - L_SURF) * e); ctx.fill()
        ctx.set_dash([14, 10]); ctx.set_line_width(3); ctx.set_source_rgba(*WARN, 0.95)
        ctx.rectangle(CX - 380, L_SURF - 2, 760, (L_BOT - 60 - L_SURF) * e); ctx.stroke()
        ctx.restore()
        draw_text(ctx, "REMOVE & REPLACE", CX, L_SURF + 150, 44, "black", (*WARN, e), align="center", sp=2)
        draw_text(ctx, "surface · binder · base", CX, L_SURF + 205, 32, "reg", (0.8, 0.8, 0.82, e), align="center")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)

    # diagram frame
    ctx.set_source_rgba(1, 1, 1, 0.18 * a * st["b_sub"])
    ctx.set_line_width(2)
    ctx.move_to(X0, L_SUB); ctx.line_to(X0, L_BOT); ctx.line_to(X1, L_BOT); ctx.line_to(X1, L_SUB)
    ctx.stroke()

def draw_labels(ctx, st):
    items = [
        ("SURFACE ASPHALT", "Smooth, sealed wearing course", L_SURF, L_BIND, st["b_surf"], "surf"),
        ("BINDER ASPHALT", "Strong structural asphalt layer", L_BIND, L_BASE, st["b_bind"], "bind"),
        ("BASE ROCK", "Compacted crushed stone", L_BASE, L_SUB, st["b_base"], "base"),
        ("SUB-BASE", "Compacted soil foundation", L_SUB, L_BOT, st["b_sub"], "sub"),
    ]
    la = st["labels"]
    if la <= 0:
        return
    for name, desc, y0, y1, b, key in items:
        if b <= 0:
            continue
        foc = st["focus"]
        dim = 1.0 if (foc is None or foc == key) else 0.35
        al = la * ease(b) * dim * st["diag"]
        ym = (y0 + y1) / 2
        ctx.set_source_rgba(1, 1, 1, 0.5 * al); ctx.set_line_width(2)
        ctx.move_to(X1 + 12, ym); ctx.line_to(X1 + 46, ym); ctx.stroke()
        ctx.arc(X1 + 12, ym, 4, 0, 6.3); ctx.fill()
        ctx.move_to(X1 + 12, y0 + 6); ctx.line_to(X1 + 12, y1 - 6); ctx.stroke()
        draw_text(ctx, name, X1 + 60, ym + 2, 31, "black", (1, 1, 1, al), sp=1.5, chrome_fill=True)
        draw_text(ctx, desc, X1 + 60, ym + 32, 22, "reg", (0.75, 0.75, 0.77, al))

def draw_sky(ctx, st, t):
    a = st["diag"]
    # sun
    if st["sun"] > 0:
        sa = st["sun"] * a
        sx, sy = 1220, 330
        g = cairo.RadialGradient(sx, sy, 10, sx, sy, 110)
        g.add_color_stop_rgba(0, 1, 0.85, 0.45, 0.45 * sa); g.add_color_stop_rgba(1, 1, 0.8, 0.4, 0)
        ctx.set_source(g); ctx.arc(sx, sy, 110, 0, 6.3); ctx.fill()
        ctx.set_source_rgba(1, 0.86, 0.5, sa)
        ctx.arc(sx, sy, 30, 0, 6.3); ctx.fill()
        ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(10):
            ang = i * math.pi / 5 + t * 0.4
            ctx.move_to(sx + 44 * math.cos(ang), sy + 44 * math.sin(ang))
            ctx.line_to(sx + 62 * math.cos(ang), sy + 62 * math.sin(ang))
        ctx.stroke()
    # rain
    if st["rain"] > 0:
        rnd = random.Random(2)
        ctx.set_line_width(2.5); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        bounce = st.get("bounce", 0)
        for i in range(90):
            x0 = rnd.uniform(X0 + 20, X1 - 20)
            sp = rnd.uniform(0.9, 1.3)
            ph = (t * sp * 0.9 + rnd.random()) % 1
            y = SKY + 10 + ph * (L_SURF - SKY - 10)
            x = x0 - ph * 30
            al = st["rain"] * a * min(1, (1 - ph) * 6) * 0.8
            ctx.set_source_rgba(*WATER, al)
            ctx.move_to(x, y - 22); ctx.line_to(x - 5, y); ctx.stroke()
            if ph > 0.92 and bounce:
                ctx.set_source_rgba(*WATER, st["rain"] * a * bounce)
                ctx.arc(x - 8, L_SURF - 10, 3, 0, 6.3); ctx.arc(x + 4, L_SURF - 14, 2.5, 0, 6.3); ctx.fill()
        # puddle film running to crack
        if st["film"] > 0:
            ctx.set_source_rgba(*WATER, 0.7 * st["film"] * a)
            for side in (-1, 1):
                ctx.move_to(CX, L_SURF - 1)
                ctx.line_to(CX + side * 260 * st["film"], L_SURF - 1)
                ctx.line_to(CX + side * 260 * st["film"], L_SURF + 0.5)
            ctx.set_line_width(5); ctx.stroke()
    # thermometer
    if st["thermo"] > 0:
        ta = st["thermo"] * a
        tx, ty0, ty1 = 1255, 270, 430
        ctx.set_source_rgba(1, 1, 1, 0.9 * ta); ctx.set_line_width(3)
        rrect(ctx, tx - 12, ty0, 24, ty1 - ty0, 12); ctx.stroke()
        ctx.arc(tx, ty1 + 12, 20, 0, 6.3); ctx.stroke()
        temp = st["temp"]  # 0 cold .. 1 warm
        col = tuple(ICE[i] * (1 - temp) + WARN[i] * temp for i in range(3))
        ctx.set_source_rgba(*col, ta)
        ctx.arc(tx, ty1 + 12, 14, 0, 6.3); ctx.fill()
        lvl = ty1 - (20 + 110 * temp)
        ctx.rectangle(tx - 6, lvl, 12, ty1 + 4 - lvl); ctx.fill()
        fy = ty1 - 75
        ctx.set_source_rgba(1, 1, 1, 0.6 * ta); ctx.set_line_width(2)
        ctx.move_to(tx - 24, fy); ctx.line_to(tx - 14, fy); ctx.stroke()
        draw_text(ctx, "32°F", tx - 30, fy + 8, 22, "bold", (1, 1, 1, 0.8 * ta), align="right")
        lab = "FREEZE" if temp < 0.45 else "THAW"
        draw_text(ctx, lab, tx - 30, ty0 + 22, 26, "black", (*col, ta), align="right", sp=1)
    # wheel
    if st["wheel"] is not None:
        wx = st["wheel"]
        wr = 58
        d = layer_offset(wx, st, 1)
        wy = L_SURF - wr + d - 2
        wa = a * st["wheel_a"]
        ctx.save(); ctx.translate(wx, wy)
        ctx.set_source_rgba(0.07, 0.07, 0.08, wa); ctx.arc(0, 0, wr, 0, 6.3); ctx.fill()
        ctx.set_source_rgba(0.75, 0.75, 0.78, wa); ctx.set_line_width(4); ctx.arc(0, 0, wr - 3, 0, 6.3); ctx.stroke()
        ctx.set_source(chrome(ctx, -26, 26, wa)); ctx.arc(0, 0, 26, 0, 6.3); ctx.fill()
        rot = wx / wr
        ctx.set_source_rgba(0.2, 0.2, 0.22, wa); ctx.set_line_width(3)
        for i in range(5):
            ang = rot + i * 2 * math.pi / 5
            ctx.move_to(8 * math.cos(ang), 8 * math.sin(ang)); ctx.line_to(24 * math.cos(ang), 24 * math.sin(ang))
        ctx.stroke()
        ctx.restore()
        if st["load"] > 0:
            la = st["load"] * wa
            for k in range(3):
                ph = (t * 1.5 + k / 3) % 1
                y = wy + wr + 18 + ph * 70
                ctx.set_source_rgba(1, 1, 1, la * math.sin(ph * math.pi) * 0.8)
                arrow(ctx, wx, y, 0, 1, 18)

def arrow(ctx, x, y, dx, dy, s):
    ctx.move_to(x - s * 0.7 * dy + 0, y - s * 0.7 * dx)
    ctx.line_to(x + s * dx, y + s * dy)
    ctx.line_to(x + s * 0.7 * dy, y + s * 0.7 * dx)
    ctx.close_path(); ctx.fill()

def draw_callout(ctx, text, px, py, tx, ty, a, color=(1, 1, 1)):
    if a <= 0:
        return
    ctx.set_source_rgba(*color, a); ctx.set_line_width(2.5)
    ctx.arc(px, py, 6, 0, 6.3); ctx.fill()
    ctx.move_to(px, py); ctx.line_to(tx, ty); ctx.stroke()
    font(ctx, 28, "black")
    tw = spaced_extent(ctx, text, 1.2)
    bx = tx - tw / 2 - 18
    ctx.set_source_rgba(0, 0, 0, 0.82 * a); rrect(ctx, bx, ty - 42, tw + 36, 52, 10); ctx.fill()
    ctx.set_source_rgba(*color, a); rrect(ctx, bx, ty - 42, tw + 36, 52, 10); ctx.stroke()
    draw_text(ctx, text, tx, ty - 6, 28, "black", (*color, a), align="center", sp=1.2)

# ---------------------------------------------------------------- captions
CAPS = [
    (16.0, 20.6, "IT STARTS SMALL", "Sun, traffic and age open a hairline crack in the surface."),
    (20.6, 25.0, "LEFT ALONE, IT GROWS", "The crack works its way down toward the binder layer."),
    (25.0, 30.5, "THEN THE RAIN COMES", "Water runs straight into the open crack..."),
    (30.5, 36.0, "WATER REACHES THE BASE", "...and soaks the crushed-stone base rock underneath."),
    (36.0, 42.5, "THEN INDIANA WINTER HITS", "Temperatures swing above and below freezing, again and again."),
    (42.5, 48.5, "ICE PRIES IT APART", "Water expands about 9% when it freezes, forcing the crack wider."),
    (48.5, 56.0, "EVERY THAW LETS IN MORE", "Each cycle opens bigger gaps for the next round of water."),
    (56.0, 61.0, "THE BASE LOSES STRENGTH", "Saturated stone shifts, and fine material washes out, leaving voids."),
    (61.0, 66.0, "THE SUB-BASE GOES SOFT", "Wet soil can no longer carry the weight above it."),
    (66.0, 70.0, "FAILURE FROM THE BOTTOM UP", "Every vehicle now pushes the unsupported pavement down."),
    (70.0, 75.0, "ALLIGATOR CRACKS, THEN POTHOLES", "What began as one small crack is now a structural failure."),
    (87.0, 92.5, "KEEP WATER OUT", "Sealing cracks early keeps the layers underneath dry and strong."),
    (92.5, 99.0, "A SIMPLE MAINTENANCE PLAN", "Small, routine work protects the whole pavement system."),
]

def draw_caption(ctx, t):
    for a, b, head, sub in CAPS:
        if a - 0.01 <= t < b + 0.01:
            al = window(t, a, b, 0.45, 0.35)
            dy = (1 - eout(prog(t, a, a + 0.6))) * 18
            draw_text(ctx, head, 140, 150 + dy, 62, "black", (1, 1, 1, al), sp=2, chrome_fill=True)
            draw_text(ctx, sub, 142, 205 + dy, 32, "reg", (0.8, 0.8, 0.82, al * ease(prog(t, a + 0.15, a + 0.7))))

STEPS = [("CRACK", 15.5, 25), ("WATER", 25, 36), ("FREEZE-THAW", 36, 56), ("FAILURE", 56, 75), ("PREVENTION", 86, 99)]

def draw_steps(ctx, t):
    al = window(t, 15.0, 75.6, 0.6, 0.6) + window(t, 85.8, 99.5, 0.6, 0.6)
    if al <= 0:
        return
    x = 140
    y = 1030
    for i, (name, a, b) in enumerate(STEPS):
        act = a <= t < b
        done = t >= b
        font(ctx, 22, "black")
        tw = spaced_extent(ctx, name, 2)
        w = tw + 60
        if act:
            ctx.set_source(chrome(ctx, y - 26, y + 14, al)); rrect(ctx, x, y - 30, w, 44, 22); ctx.fill()
            col = (0.05, 0.05, 0.05, al)
        else:
            ctx.set_source_rgba(1, 1, 1, (0.35 if done else 0.18) * al); ctx.set_line_width(2)
            rrect(ctx, x, y - 30, w, 44, 22); ctx.stroke()
            col = (1, 1, 1, (0.75 if done else 0.4) * al)
        ctx.set_source_rgba(*col)
        ctx.arc(x + 24, y - 8, 9, 0, 6.3); ctx.fill()
        draw_text(ctx, str(i + 1), x + 24, y - 1, 15, "black",
                  (1, 1, 1, al) if act else (0, 0, 0, al), align="center")
        draw_text(ctx, name, x + 42, y, 22, "black", col, sp=2)
        x += w + 16
    # small logo bottom-right
    draw_logo(ctx, 1790, 1010, 120, al)

def draw_logo(ctx, cx, cy, w, a, shine=None):
    if a <= 0:
        return
    lw, lh = LOGO.get_width(), LOGO.get_height()
    s = w / lw
    ctx.save()
    ctx.translate(cx - w / 2, cy - lh * s / 2)
    ctx.scale(s, s)
    ctx.set_source_surface(LOGO, 0, 0)
    ctx.paint_with_alpha(a)
    if shine is not None and 0 < shine < 1:
        ctx.set_operator(cairo.OPERATOR_ADD)
        g = cairo.LinearGradient(-lw * 0.6 + shine * lw * 2.2, 0, -lw * 0.3 + shine * lw * 2.2, lh)
        g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(0.5, 1, 1, 1, 0.45 * a)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(g)
        ctx.mask_surface(LOGO, 0, 0)
    ctx.restore()

# ---------------------------------------------------------------- state over time
def state(t):
    st = dict(diag=0, b_sub=0, b_base=0, b_bind=0, b_surf=0, labels=0, focus=None,
              crack=0, cw=3, water=0, wet=0, ice=0, voids=0, mud=0, pump=0, sink=0, heave=0,
              gator=0, pothole=0, fill=0, sun=0, rain=0, film=0, thermo=0, temp=1, wheel=None,
              wheel_a=0, load=0, excavate=0, bounce=0)
    # main diagram visible 5.5 .. 75.5 and again 86..99
    st["diag"] = window(t, 5.0, 75.6, 0.6, 0.7) + window(t, 85.6, 99.6, 0.7, 0.6)
    if t < 80:
        st["b_sub"] = prog(t, 6.0, 7.0)
        st["b_base"] = prog(t, 7.4, 8.4)
        st["b_bind"] = prog(t, 8.8, 9.8)
        st["b_surf"] = prog(t, 10.2, 11.2)
        st["labels"] = 1
        if 6 <= t < 15:
            st["focus"] = "sub" if t < 7.4 else "base" if t < 8.8 else "bind" if t < 10.2 else "surf" if t < 12.6 else None
        # crack
        st["sun"] = window(t, 15.6, 22.5, 0.6, 0.8)
        st["crack"] = 60 * eout(prog(t, 16.8, 19.8)) + 80 * ease(prog(t, 21.0, 24.5))
        st["cw"] = 2 + 3 * prog(t, 16.8, 24.5)
        if 15.5 <= t < 25:
            st["focus"] = "surf" if t < 20.6 else "bind"
        # traffic
        if 17.5 <= t < 21:
            st["wheel"] = X0 - 80 + (DW + 160) * prog(t, 17.5, 21)
            st["wheel_a"] = 1
        # rain
        st["rain"] = window(t, 25.0, 36.5, 0.6, 0.8)
        st["film"] = ease(prog(t, 25.8, 27.5)) * (1 - ease(prog(t, 35.5, 36.5)))
        st["water"] = 140 * ease(prog(t, 26.5, 30.5))
        st["wet"] = 0.55 * ease(prog(t, 30.5, 35.0))
        if 25 <= t < 36:
            st["focus"] = "base" if t >= 30.5 else None
        # freeze-thaw: 3 cycles from 38.5, 5.6s each
        st["thermo"] = window(t, 36.2, 56.0, 0.6, 0.6)
        ft0, cyc = 38.5, 5.6
        st["temp"] = 1
        ncycles = 0
        if t >= 36.2:
            st["temp"] = 1 - 0.3 * prog(t, 36.2, 38.5)
        for k in range(3):
            c0 = ft0 + k * cyc
            fr = ease(prog(t, c0, c0 + 1.8)) * (1 - ease(prog(t, c0 + 3.2, c0 + 4.8)))
            if c0 <= t < c0 + cyc:
                st["temp"] = 0.7 - 0.7 * ease(prog(t, c0, c0 + 1.4)) + 0.75 * ease(prog(t, c0 + 3.0, c0 + 4.4))
                st["ice"] = fr
                st["heave"] = 14 * fr
            if t >= c0 + 1.5:
                ncycles = k + 1
        if t >= ft0 + 3 * cyc:
            st["temp"] = 1 - 0.3 * prog(t, ft0 + 3 * cyc, ft0 + 3 * cyc + 1)
        grow = sum(ease(prog(t, ft0 + k * cyc + 0.3, ft0 + k * cyc + 1.8)) for k in range(3))
        st["cw"] += 5 * grow + 5 * st["ice"]
        st["wet"] += 0.15 * grow
        st["voids"] = 0.15 * grow
        st["ft_count"] = ncycles
        if 36 <= t < 56:
            st["focus"] = "base" if st["ice"] > 0.3 else None
        # bottom-up failure
        st["voids"] += 0.55 * ease(prog(t, 56.3, 60.0))
        st["pump"] = window(t, 57.0, 75.6, 0.8, 0.5) * 0.9
        st["mud"] = ease(prog(t, 61.0, 64.5))
        st["sink"] = 26 * ease(prog(t, 66.0, 71.5)) + 10 * ease(prog(t, 71.5, 74))
        st["gator"] = ease(prog(t, 69.0, 72.5))
        st["pothole"] = ease(prog(t, 72.6, 74.2))
        if 56 <= t < 76:
            st["focus"] = "base" if t < 61 else "sub" if t < 66 else None
        if 65.2 <= t < 73.5:
            # repeated traffic
            ph = ((t - 65.2) / 2.6) % 1
            st["wheel"] = X0 - 80 + (DW + 160) * ph
            st["wheel_a"] = min(1, math.sin(ph * math.pi) * 4)
            st["load"] = 1
        if t >= 70:
            st["rain"] = 0.6 * window(t, 72.5, 75.6, 0.5, 0.6)
    else:
        # prevention scene: healthy section, crack gets filled
        for k in ("b_sub", "b_base", "b_bind", "b_surf"):
            st[k] = 1
        st["labels"] = 1 - ease(prog(t, 86, 87))
        st["crack"] = 45
        st["cw"] = 4
        st["fill"] = ease(prog(t, 89.0, 91.8))
        st["rain"] = window(t, 92.8, 99.6, 0.6, 0.6)
        st["bounce"] = 1
    return st

# ---------------------------------------------------------------- scene pieces
def draw_ft_counter(ctx, t, st):
    a = window(t, 38.0, 56.0, 0.5, 0.6) * st["diag"]
    if a <= 0:
        return
    n = st.get("ft_count", 0)
    x, y = 140, 300
    draw_text(ctx, "FREEZE-THAW CYCLES", x, y, 22, "black", (0.8, 0.8, 0.82, a), sp=2)
    for k in range(3):
        on = k < n
        ctx.set_source_rgba(*(ICE if on else (1, 1, 1)), (1 if on else 0.25) * a)
        ctx.arc(x + 16 + k * 40, y + 30, 13, 0, 6.3)
        ctx.fill() if on else (ctx.set_line_width(2), ctx.stroke())
    draw_text(ctx, "+ MORE EVERY WINTER", x + 140, y + 38, 22, "black", (1, 1, 1, a * ease(prog(t, 52, 53))), sp=1.5)

def draw_upward(ctx, t, st):
    a = window(t, 66.0, 75.5, 0.6, 0.6) * st["diag"]
    if a <= 0:
        return
    for k, xo in enumerate((-240, 0, 240)):
        for j in range(3):
            ph = (t * 0.6 + j / 3 + k * 0.17) % 1
            y = L_SUB + 70 - ph * 260
            x = CX + xo + (60 if xo == 0 else 0)
            ctx.set_source_rgba(*WARN, a * math.sin(ph * math.pi) * 0.9)
            ctx.set_line_width(5)
            ctx.move_to(x, y + 30); ctx.line_to(x, y + 6); ctx.stroke()
            arrow(ctx, x, y, 0, -1, 16)

def draw_scene_callouts(ctx, t, st):
    d = st["diag"]
    draw_callout(ctx, "HAIRLINE CRACK", CX, L_SURF + 10, CX - 380, 360,
                 window(t, 18.0, 25.0, 0.5, 0.5) * d)
    draw_callout(ctx, "SATURATED BASE", CX + 230, L_BASE + 70, 960, 370,
                 window(t, 32.0, 36.0, 0.5, 0.5) * d, WATER)
    draw_callout(ctx, "ICE EXPANDS ~9%", CX, L_SURF + 40, CX - 280, 380,
                 (window(t, 39.4, 42.3, 0.4, 0.4) + window(t, 45.0, 47.9, 0.4, 0.4)) * d, ICE)
    draw_callout(ctx, "VOIDS", CX + 120, L_BASE + 60, 1000, 380,
                 window(t, 57.5, 61.0, 0.5, 0.4) * d)
    draw_callout(ctx, "SOFT, WET SOIL", CX + 300, L_SUB + 70, 1010, 390,
                 window(t, 62.0, 65.8, 0.5, 0.4) * d)
    draw_callout(ctx, "ALLIGATOR CRACKING", CX + 270, L_SURF + 30, 1010, 380,
                 window(t, 70.2, 72.6, 0.4, 0.3) * d, WARN)
    draw_callout(ctx, "POTHOLE", CX - 60, L_SURF + 60, CX - 330, 380,
                 window(t, 73.0, 75.5, 0.4, 0.4) * d, WARN)
    draw_callout(ctx, "CRACK SEALED", CX + 30, L_SURF - 2, CX + 330, 370,
                 window(t, 91.8, 99.5, 0.4, 0.6) * d)

def draw_nozzle(ctx, t):
    a = window(t, 87.6, 92.6, 0.6, 0.6)
    if a <= 0:
        return
    y = 300 + 90 * ease(prog(t, 87.6, 89.0)) - 90 * ease(prog(t, 91.8, 92.6))
    ctx.set_source(chrome(ctx, y - 60, y + 40, a))
    ctx.move_to(CX - 26, y - 70); ctx.line_to(CX + 26, y - 70); ctx.line_to(CX + 10, y + 20)
    ctx.line_to(CX - 10, y + 20); ctx.close_path(); ctx.fill()
    ctx.rectangle(CX - 40, y - 110, 80, 40); ctx.fill()
    if 89.0 <= t < 91.8:
        ctx.set_source_rgba(0.06, 0.06, 0.07, a)
        ctx.rectangle(CX - 4, y + 20, 8, L_SURF - y - 20); ctx.fill()

CHECKS = [
    ("CRACK FILLING", "Seals cracks before water gets in", 92.9),
    ("SPOT PATCHING", "Fixes small failed areas early", 93.6),
    ("SEALCOATING", "Shields from sun, water and oil", 94.3),
    ("ROUTINE INSPECTIONS", "Catches problems while they're small", 95.0),
]

def draw_checklist(ctx, t):
    base_a = window(t, 92.5, 99.6, 0.5, 0.6)
    if base_a <= 0:
        return
    for i, (name, desc, t0) in enumerate(CHECKS):
        a = base_a * ease(prog(t, t0, t0 + 0.5))
        if a <= 0:
            continue
        dx = (1 - eout(prog(t, t0, t0 + 0.6))) * 40
        x, y = 1390 + dx, 520 + i * 112
        ctx.set_source(chrome(ctx, y - 22, y + 22, a)); ctx.arc(x + 20, y - 10, 21, 0, 6.3); ctx.fill()
        ctx.set_source_rgba(0.05, 0.05, 0.05, a); ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(x + 10, y - 10); ctx.line_to(x + 17, y - 2); ctx.line_to(x + 31, y - 19); ctx.stroke()
        draw_text(ctx, name, x + 56, y, 29, "black", (1, 1, 1, a), sp=1.2, chrome_fill=True)
        draw_text(ctx, desc, x + 56, y + 32, 21, "reg", (0.75, 0.75, 0.77, a))

# ---------------------------------------------------------------- comparison scene (75.5 - 86)
def draw_compare(ctx, t):
    A = window(t, 75.8, 86.0, 0.7, 0.6)
    if A <= 0:
        return
    draw_text(ctx, "SMALL FIX NOW  —  OR  —  BIG REPAIR LATER", 960, 150, 58, "black",
              (1, 1, 1, A), align="center", sp=2, chrome_fill=True)
    draw_text(ctx, "The same crack, two very different outcomes.", 960, 205, 32, "reg",
              (0.8, 0.8, 0.82, A * ease(prog(t, 76.2, 76.9))), align="center")
    panels = [
        (120, "FIX IT EARLY", "Crack filling & spot patching", 0.14, "$",
         dict(crack=40, cw=4, fill=1), 76.6, (1, 1, 1)),
        (990, "WAIT AND SEE", "Dig out & rebuild every layer", 1.0, "$$$$",
         dict(excavate=1, crack=0), 77.6, WARN),
    ]
    for px, head, sub, cost, sym, extra, t0, col in panels:
        a = A * ease(prog(t, t0, t0 + 0.7))
        if a <= 0:
            continue
        pw = 810
        ctx.set_source_rgba(1, 1, 1, 0.05 * a); rrect(ctx, px, 255, pw, 700, 22); ctx.fill()
        ctx.set_source_rgba(*col, 0.45 * a); ctx.set_line_width(2); rrect(ctx, px, 255, pw, 700, 22); ctx.stroke()
        draw_text(ctx, head, px + 40, 320, 44, "black", (*col, a), sp=2, chrome_fill=(col == (1, 1, 1)))
        draw_text(ctx, sub, px + 40, 362, 28, "reg", (0.8, 0.8, 0.82, a))
        # mini section
        st = state(12)  # healthy
        st.update(dict(diag=1, labels=0, focus=None, wheel=None, sun=0, rain=0, thermo=0))
        st.update(extra)
        if extra.get("excavate"):
            st["excavate"] = ease(prog(t, t0 + 0.4, t0 + 1.6))
        if extra.get("fill"):
            st["fill"] = ease(prog(t, t0 + 0.4, t0 + 1.4))
        s = 0.6
        ctx.save()
        ctx.translate(px + 40 - X0 * s, 400 - L_SURF * s + 30)
        ctx.scale(s, s)
        ctx.rectangle(X0, L_SURF - 20, DW, L_BOT - L_SURF + 20); ctx.clip()
        draw_section(ctx, st, t)
        ctx.restore()
        # cost bar
        by = 860
        draw_text(ctx, "RELATIVE COST", px + 40, by - 18, 20, "black", (0.7, 0.7, 0.72, a), sp=2)
        ctx.set_source_rgba(1, 1, 1, 0.12 * a); rrect(ctx, px + 40, by, pw - 80, 40, 20); ctx.fill()
        bw = (pw - 80) * cost * eout(prog(t, t0 + 1.0, t0 + 2.4))
        if bw > 4:
            if col == (1, 1, 1):
                ctx.set_source(chrome(ctx, by, by + 40, a))
            else:
                ctx.set_source_rgba(*col, a)
            rrect(ctx, px + 40, by, max(bw, 40), 40, 20); ctx.fill()
        sa = a * ease(prog(t, t0 + 2.0, t0 + 2.5))
        if cost < 0.5:
            draw_text(ctx, sym, px + 40 + max(bw, 40) + 16, by + 32, 36, "black", (*col, sa))
        else:
            draw_text(ctx, sym, px + 40 + bw - 20, by + 32, 36, "black", (1, 1, 1, sa), align="right")
    draw_text(ctx, "Illustrative comparison. Actual costs depend on site conditions.", 960, 1000, 22,
              "reg", (0.6, 0.6, 0.62, A * ease(prog(t, 79, 80))), align="center")

# ---------------------------------------------------------------- intro / outro
def draw_intro(ctx, t):
    a = window(t, 0.2, 5.3, 0.9, 0.6)
    if a <= 0:
        return
    s = 1 + 0.04 * prog(t, 0, 5.3)
    draw_logo(ctx, 960, 430, 640 * s, a, shine=prog(t, 1.2, 2.6))
    ta = a * ease(prog(t, 2.0, 2.8))
    draw_text(ctx, "WHAT HAPPENS WHEN A CRACK GOES UNFIXED?", 960, 860, 52, "black",
              (1, 1, 1, ta), align="center", sp=2, chrome_fill=True)
    draw_text(ctx, "A look beneath your parking lot.", 960, 915, 32, "reg",
              (0.78, 0.78, 0.8, a * ease(prog(t, 2.6, 3.3))), align="center")

def draw_layers_title(ctx, t):
    al = window(t, 5.2, 16.0, 0.6, 0.4)
    if al <= 0:
        return
    head, sub = ("WHAT'S UNDER YOUR PAVEMENT", "A healthy parking lot is a system of layers...") if t < 11.5 else \
                ("EVERY LAYER SUPPORTS THE ONE ABOVE", "...and each one depends on staying dry.")
    k = window(t, 5.2, 11.5, 0.6, 0.35) if t < 11.5 else window(t, 11.5, 16.0, 0.45, 0.4)
    draw_text(ctx, head, 140, 150, 62, "black", (1, 1, 1, k), sp=2, chrome_fill=True)
    draw_text(ctx, sub, 142, 205, 32, "reg", (0.8, 0.8, 0.82, k))

def draw_outro(ctx, t):
    a = window(t, 99.6, DUR + 1, 0.9, 0.1) * (1 - ease(prog(t, DUR - 1.0, DUR)))
    if a <= 0:
        return
    draw_logo(ctx, 960, 400, 560, a, shine=prog(t, 100.4, 101.8))
    draw_text(ctx, "PROTECT YOUR PAVEMENT. PROTECT YOUR INVESTMENT.", 960, 790, 48, "black",
              (1, 1, 1, a * ease(prog(t, 100.6, 101.4))), align="center", sp=2, chrome_fill=True)
    draw_text(ctx, "Ask Stubbs Asphalt about a preventive maintenance plan.", 960, 850, 34, "reg",
              (0.82, 0.82, 0.84, a * ease(prog(t, 101.2, 101.9))), align="center")
    if CONTACT:
        draw_text(ctx, CONTACT, 960, 930, 36, "black", (1, 1, 1, a * ease(prog(t, 101.8, 102.5))),
                  align="center", sp=2)

CONTACT = os.environ.get("STUBBS_CONTACT", "")

# ---------------------------------------------------------------- frame
def background(ctx):
    g = cairo.RadialGradient(960, 520, 50, 960, 540, 1150)
    g.add_color_stop_rgb(0, 0.085, 0.085, 0.09)
    g.add_color_stop_rgb(1, 0.0, 0.0, 0.0)
    ctx.set_source(g); ctx.paint()

def init():
    global TEX, LOGO
    TEX = make_textures()
    LOGO = load_logo()

def load_logo():
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGB")).astype(np.float32)
    al = im.max(axis=2)  # screen-style alpha: identical to original over black
    bgra = np.dstack([im[..., 2], im[..., 1], im[..., 0], al]).clip(0, 255).astype(np.uint8)
    h, w = al.shape
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = bytearray(stride * h)
    arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, stride)
    arr[:, : w * 4] = bgra.reshape(h, w * 4)
    return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)

def render(i):
    t = i / FPS
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    background(ctx)
    st = state(t)
    draw_intro(ctx, t)
    if st["diag"] > 0:
        draw_sky(ctx, st, t)
        draw_section(ctx, st, t)
        draw_labels(ctx, st)
        draw_upward(ctx, t, st)
        draw_scene_callouts(ctx, t, st)
        draw_ft_counter(ctx, t, st)
        draw_nozzle(ctx, t)
    draw_layers_title(ctx, t)
    draw_caption(ctx, t)
    draw_checklist(ctx, t)
    draw_compare(ctx, t)
    draw_steps(ctx, t)
    draw_outro(ctx, t)
    surf.flush()
    return bytes(surf.get_data())

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        init()
        for ts in sys.argv[2:]:
            t = float(ts)
            data = render(int(round(t * FPS)))
            s = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, W, H)
            s.write_to_png(os.path.join(OUT, f"still_{ts}.png"))
        return
    n = int(DUR * FPS)
    audio = os.path.join(HERE, "assets", "music.wav")
    out = os.path.join(OUT, "stubbs_explainer.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if os.path.exists(audio):
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init) as pool:
        for k, data in enumerate(pool.imap(render, range(n), chunksize=6)):
            p.stdin.write(data)
            if k % 300 == 0:
                print(f"frame {k}/{n}", flush=True)
    p.stdin.close(); p.wait()
    print("wrote", out)

if __name__ == "__main__":
    main()
