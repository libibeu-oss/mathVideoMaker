"""mathviz_lite — a dependency-light animation engine for math explainer videos.

Use it when Manim is not available (e.g. Claude's cloud sandbox, where PyPI may be
blocked). It needs only numpy, Pillow (with raqm for RTL/Hebrew), opencv-python and
the ffmpeg binary — all common in Python environments.

Highlights
- Proper right-to-left text (Hebrew/Arabic) through Pillow's raqm layout engine.
- Antialiased shapes (opencv LINE_AA, sub-pixel precision).
- Tween-based animation: FadeIn / FadeOut / Create / Write / Tween / Morph / Lagged / Func.
- Built-in guard rails, the same idea as SafeScene in mathviz.py:
    * every Text is checked for glyphs missing from the font  -> "[glyph] WARN ..."
    * after every play()/wait() the visible objects are checked for leaving the safe
      area and for text-on-text overlap                        -> "[layout] WARN ..."
    * at the end:  "[layout] DONE found N layout issues"  (must be 0 before delivery)
- scene.snapshot("x.png") saves the current frame so you can look at it.

Coordinates are pixels on a 1920x1080 canvas, origin top-left, y pointing down.
Use Axes for math coordinates.

Minimal example
    from mathviz_lite import *
    s = Scene("Demo", out_dir=".")
    t = s.title("שלום עולם")
    sq = Rect((960, 540), 300, 300, fill=BLUE, fill_opacity=0.5)
    s.play(Create(sq), run_time=1.2)
    s.caption("ריבוע אחד, באמצע המסך.")
    s.wait(2)
    s.close()          # -> ./Demo.mp4
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, features

# --------------------------------------------------------------------------------------
# Canvas & palette (dark theme, same spirit as mathviz.py)
# --------------------------------------------------------------------------------------
W, H = 1920, 1080
FPS = 30
SAFE = 48                     # safe-area margin in px

BG = (15, 20, 25)
WHITE = (240, 244, 248)
GREY = (150, 160, 175)
DIM = (70, 80, 95)
BLUE = (91, 156, 255)
YELLOW = (255, 209, 102)
GREEN = (94, 214, 140)
ORANGE = (255, 146, 92)
RED = (255, 99, 110)
PURPLE = (180, 140, 255)
TEAL = (64, 200, 200)

HEB_RANGE = (0x0590, 0x05FF)

# --------------------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------------------
_FONT_CANDIDATES = [
    os.environ.get("MATHVIZ_FONT", ""),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Rubik[wght].ttf"),
    "/usr/share/fonts/truetype/rubik/Rubik[wght].ttf",
    "/Library/Fonts/Arial Hebrew.ttc",
    "/System/Library/Fonts/ArialHB.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _find_font() -> str:
    for p in _FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise FileNotFoundError("No usable font found. Set MATHVIZ_FONT=/path/to/font.ttf")


FONT_PATH = _find_font()
_LAYOUT = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC
if _LAYOUT != ImageFont.Layout.RAQM:
    print("[glyph] WARN Pillow has no raqm: right-to-left text may render reversed", file=sys.stderr)

_cmap_cache: dict[str, set[int]] = {}


def _cmap(path: str) -> set[int]:
    if path not in _cmap_cache:
        try:
            from fontTools.ttLib import TTFont
            _cmap_cache[path] = set(TTFont(path, fontNumber=0).getBestCmap().keys())
        except Exception:
            _cmap_cache[path] = set()
    return _cmap_cache[path]


_font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}


def get_font(size: int, weight: int = 500, path: str | None = None) -> ImageFont.FreeTypeFont:
    path = path or FONT_PATH
    key = (path, int(size), int(weight))
    if key not in _font_cache:
        f = ImageFont.truetype(path, int(size), layout_engine=_LAYOUT)
        try:  # variable font: set weight axis
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _font_cache[key] = f
    return _font_cache[key]


_MATH_RUN = re.compile(r"[0-9A-Za-z\u00b2\u00b3(\u221a][0-9A-Za-z\u00b2\u00b3\u00d7\u00b7+\-\u2212=<>\u2264\u2265\u2260()/.,^\u221a ]*[0-9A-Za-z\u00b2\u00b3)]|[0-9A-Za-z]")


def split_bidi(s: str):
    """Split a right-to-left string into [(segment, 'rtl'|'ltr'), ...] in logical order,
    where 'ltr' segments are math runs."""
    out, i = [], 0
    for m in _MATH_RUN.finditer(s):
        if m.start() > i:
            out.append((s[i:m.start()], "rtl"))
        out.append((m.group(0), "ltr"))
        i = m.end()
    if i < len(s):
        out.append((s[i:], "rtl"))
    return out


def isolate_math(s: str) -> str:
    """Wrap left-to-right math runs in Unicode isolates (LRI ... PDI) so that inside a
    Hebrew sentence "3² + 4² = 5²" keeps its order instead of being reversed by bidi."""
    if not has_rtl(s):
        return s
    return _MATH_RUN.sub(lambda m: "\u2066" + m.group(0) + "\u2069", s)


def has_rtl(s: str) -> bool:
    return any(HEB_RANGE[0] <= ord(c) <= HEB_RANGE[1] or 0x0600 <= ord(c) <= 0x06FF for c in s)


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def smooth(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def linear(t: float) -> float:
    return min(max(t, 0.0), 1.0)


def ease_out_back(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def lerp(a, b, t):
    if isinstance(a, tuple):
        return tuple(lerp(x, y, t) for x, y in zip(a, b))
    if isinstance(a, np.ndarray):
        return a + (b - a) * t
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def _blend_region(frame: np.ndarray, overlay: np.ndarray, mask: np.ndarray, x0, y0, opacity: float):
    """Alpha-blend overlay (h,w,3) using mask (h,w) in 0..1 onto frame at (x0,y0)."""
    h, w = mask.shape
    fx0, fy0 = max(x0, 0), max(y0, 0)
    fx1, fy1 = min(x0 + w, frame.shape[1]), min(y0 + h, frame.shape[0])
    if fx1 <= fx0 or fy1 <= fy0:
        return
    ox0, oy0 = fx0 - x0, fy0 - y0
    m = mask[oy0:oy0 + (fy1 - fy0), ox0:ox0 + (fx1 - fx0), None] * opacity
    region = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    ov = overlay[oy0:oy0 + (fy1 - fy0), ox0:ox0 + (fx1 - fx0)].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (region * (1 - m) + ov * m).astype(np.uint8)


# --------------------------------------------------------------------------------------
# Mobjects
# --------------------------------------------------------------------------------------
class Mob:
    z = 0
    layout_check = True        # set False for decorative/background objects

    def __init__(self):
        self.opacity = 1.0
        self.offset = (0.0, 0.0)   # transient shift used by FadeIn/FadeOut
        self.scale = 1.0

    def draw(self, frame: np.ndarray):  # pragma: no cover - abstract
        raise NotImplementedError

    def bbox(self):
        return None


class Text(Mob):
    """A single line of text. RTL (Hebrew) is shaped automatically.

    pos is the anchor point; anchor uses Pillow notation: 'mm' centre, 'rm' right-middle,
    'lm' left-middle, 'mt' middle-top ...
    """
    z = 10

    def __init__(self, text: str, pos=(W / 2, H / 2), size: int = 48, color=WHITE,
                 weight: int = 500, anchor: str = "mm", max_width: float | None = None,
                 glow: bool = False, z: int | None = None):
        super().__init__()
        self.text, self.pos, self.size, self.color = text, pos, size, color
        self.weight, self.anchor, self.glow = weight, anchor, glow
        self.reveal = 1.0      # 0..1 for Write()
        if z is not None:
            self.z = z
        self._check_glyphs()
        self._sprite = self._render()
        if max_width and self._sprite.shape[1] > max_width:
            self.size = int(self.size * max_width / self._sprite.shape[1])
            self._sprite = self._render()

    def _check_glyphs(self):
        cm = _cmap(FONT_PATH)
        if not cm:
            return
        missing = sorted({c for c in self.text
                          if not c.isspace() and ord(c) not in cm and not 0x2066 <= ord(c) <= 0x2069})
        if missing:
            print(f"[glyph] WARN font lacks {missing} in text {self.text!r} -> will show as boxes."
                  f" Rephrase, or draw the symbol as a shape.", file=sys.stderr)

    def _render(self) -> np.ndarray:
        """Render to an alpha sprite.

        Mixed Hebrew + math is laid out by hand: the text is split into right-to-left
        segments and left-to-right math runs ("n = 2", "3² + 4² = 5²"), each segment is
        shaped on its own, and the segments are placed right-to-left. This keeps math in
        reading order on every platform, independent of how the bidi library treats
        neutrals such as "=" next to digits."""
        f = get_font(self.size, self.weight)
        rtl = has_rtl(self.text)
        raqm = _LAYOUT == ImageFont.Layout.RAQM
        segs = split_bidi(self.text) if rtl else [(self.text, "ltr")]
        order = list(reversed(segs)) if rtl else segs
        kw = lambda d: {"direction": d} if raqm else {}
        widths = [f.getlength(t, **kw(d)) for t, d in order]
        total = sum(widths)
        asc, desc = f.getmetrics()
        pad = int(self.size * 0.35) + (12 if self.glow else 0)
        w, h = int(math.ceil(total)) + 2 * pad, asc + desc + 2 * pad
        img = Image.new("L", (max(w, 1), max(h, 1)), 0)
        d = ImageDraw.Draw(img)
        x, base = float(pad), pad + asc
        for (t, dr), wd in zip(order, widths):
            d.text((x, base), t, font=f, fill=255, anchor="ls", **kw(dr))
            x += wd
        a = np.asarray(img, dtype=np.float32) / 255.0
        self._rtl = rtl
        # stable ink box (advance width x cap-height..baseline) so anchoring does not jitter
        top = base + f.getbbox("Hא", anchor="ls")[1]
        self._ink = (pad, top, pad + total, base + self.size * 0.08)
        if self.glow:
            g = cv2.GaussianBlur(a, (0, 0), self.size * 0.18) * 0.55
            self._glow = g
        return a

    def set_text(self, text: str):
        if text != self.text:
            self.text = text
            self._check_glyphs()
            self._sprite = self._render()

    # geometry -------------------------------------------------------------------------
    def _topleft(self, scale=1.0):
        ix0, iy0, ix1, iy1 = [v * scale for v in self._ink]
        iw, ih = ix1 - ix0, iy1 - iy0
        ax, ay = self.anchor[0], self.anchor[1]
        px, py = self.pos[0] + self.offset[0], self.pos[1] + self.offset[1]
        ox = {"l": 0, "m": iw / 2, "r": iw}[ax]
        oy = {"t": 0, "m": ih / 2, "b": ih, "s": ih}[ay]
        return px - ox - ix0, py - oy - iy0

    def bbox(self):
        ix0, iy0, ix1, iy1 = [v * self.scale for v in self._ink]
        tx, ty = self._topleft(self.scale)
        return (tx + ix0, ty + iy0, tx + ix1, ty + iy1)

    @property
    def width(self):
        return (self._ink[2] - self._ink[0]) * self.scale

    @property
    def height(self):
        return (self._ink[3] - self._ink[1]) * self.scale

    def draw(self, frame):
        if self.opacity <= 0.003:
            return
        a = self._sprite
        glow = getattr(self, "_glow", None) if self.glow else None
        if abs(self.scale - 1.0) > 1e-3:
            nw = max(1, int(a.shape[1] * self.scale)); nh = max(1, int(a.shape[0] * self.scale))
            a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_LINEAR)
            if glow is not None:
                glow = cv2.resize(glow, (nw, nh), interpolation=cv2.INTER_LINEAR)
        if self.reveal < 1.0:
            a = a.copy()
            cut = int(a.shape[1] * self.reveal)
            if self._rtl:
                a[:, : a.shape[1] - cut] = 0
            else:
                a[:, cut:] = 0
            if glow is not None:
                glow = glow * self.reveal
        tx, ty = self._topleft(self.scale)
        x0, y0 = int(round(tx)), int(round(ty))
        if glow is not None:
            ov = np.empty((*glow.shape, 3), np.uint8); ov[:] = self.color
            _blend_region(frame, ov, glow, x0, y0, self.opacity)
        ov = np.empty((*a.shape, 3), np.uint8); ov[:] = self.color
        _blend_region(frame, ov, a, x0, y0, self.opacity)


class Shape(Mob):
    """Polygon / polyline in pixel coordinates."""
    z = 0

    def __init__(self, points, fill=None, fill_opacity=0.0, stroke=WHITE, stroke_width=4.0,
                 closed=True, stroke_opacity=1.0, z: int | None = None):
        super().__init__()
        self.points = np.asarray(points, dtype=np.float64)
        self.fill, self.fill_opacity = fill, fill_opacity
        self.stroke, self.stroke_width, self.stroke_opacity = stroke, stroke_width, stroke_opacity
        self.closed = closed
        self.progress = 1.0      # 0..1 portion of outline drawn (Create)
        self.fill_progress = 1.0
        if z is not None:
            self.z = z

    def center(self):
        return self.points.mean(axis=0)

    def _pts(self):
        p = self.points
        if abs(self.scale - 1) > 1e-6:
            c = p.mean(axis=0)
            p = c + (p - c) * self.scale
        return p + np.array(self.offset)

    def bbox(self):
        p = self._pts()
        r = self.stroke_width / 2 if self.stroke is not None else 0
        return (p[:, 0].min() - r, p[:, 1].min() - r, p[:, 0].max() + r, p[:, 1].max() + r)

    def _partial(self, p):
        pts = np.vstack([p, p[:1]]) if self.closed else p
        if self.progress >= 1.0:
            return pts
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        total = seg.sum()
        target = total * max(self.progress, 0.0)
        out = [pts[0]]
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= target:
                t = (target - acc) / L if L > 0 else 0
                out.append(pts[i] + (pts[i + 1] - pts[i]) * t)
                break
            out.append(pts[i + 1])
            acc += L
        return np.array(out)

    def draw(self, frame):
        if self.opacity <= 0.003:
            return
        p = self._pts()
        x0, y0, x1, y1 = self.bbox()
        pad = 4
        x0, y0 = int(math.floor(x0)) - pad, int(math.floor(y0)) - pad
        x1, y1 = int(math.ceil(x1)) + pad, int(math.ceil(y1)) + pad
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0 or x1 < 0 or y1 < 0 or x0 > frame.shape[1] or y0 > frame.shape[0]:
            return
        local = ((p - [x0, y0]) * 16).round().astype(np.int32)
        if self.fill is not None and self.fill_opacity > 0 and self.fill_progress > 0 and self.closed:
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [local], 255, cv2.LINE_AA, shift=4)
            ov = np.empty((h, w, 3), np.uint8); ov[:] = self.fill
            _blend_region(frame, ov, m.astype(np.float32) / 255, x0, y0,
                          self.opacity * self.fill_opacity * self.fill_progress)
        if self.stroke is not None and self.stroke_width > 0 and self.progress > 0:
            part = ((self._partial(p) - [x0, y0]) * 16).round().astype(np.int32)
            m = np.zeros((h, w), np.uint8)
            cv2.polylines(m, [part], False, 255, max(1, int(round(self.stroke_width))), cv2.LINE_AA, shift=4)
            ov = np.empty((h, w, 3), np.uint8); ov[:] = self.stroke
            _blend_region(frame, ov, m.astype(np.float32) / 255, x0, y0, self.opacity * self.stroke_opacity)


def Line(p1, p2, color=WHITE, width=4.0, **kw):
    return Shape([p1, p2], stroke=color, stroke_width=width, closed=False, **kw)


def Polyline(points, color=WHITE, width=4.0, **kw):
    return Shape(points, stroke=color, stroke_width=width, closed=False, **kw)


def Polygon(points, **kw):
    return Shape(points, **kw)


def Rect(center, w, h, **kw):
    cx, cy = center
    return Shape([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                  (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], **kw)


def RoundRect(center, w, h, r=16, **kw):
    cx, cy = center
    r = min(r, w / 2, h / 2)
    pts = []
    corners = [(cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0),
               (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)]
    for ccx, ccy, a0 in corners:
        for k in range(9):
            a = math.radians(a0 + 90 * k / 8)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return Shape(pts, **kw)


def Circle(center, r, n=72, **kw):
    cx, cy = center
    return Shape([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
                  for k in range(n)], **kw)


def Arrow(p1, p2, color=WHITE, width=5.0, head=22, **kw):
    """Returns a Group: shaft + filled head."""
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1
    L = np.linalg.norm(d) or 1
    u = d / L
    n = np.array([-u[1], u[0]])
    base = p2 - u * head
    shaft = Line(p1, base + u * 2, color=color, width=width, **kw)
    tip = Shape([p2, base + n * head * 0.55, base - n * head * 0.55], fill=color, fill_opacity=1,
                stroke=None, **kw)
    return Group(shaft, tip)


def RightAngleMark(corner, d1, d2, size=26, color=YELLOW, width=3):
    c = np.array(corner, float)
    u1 = np.array(d1, float); u1 /= np.linalg.norm(u1)
    u2 = np.array(d2, float); u2 /= np.linalg.norm(u2)
    return Polyline([c + u1 * size, c + (u1 + u2) * size, c + u2 * size], color=color, width=width)


class Group(Mob):
    """Container. opacity/offset/scale act as multipliers on children."""

    def __init__(self, *mobs):
        super().__init__()
        self.mobs = list(mobs)
        self.layout_check = False   # children are checked individually

    def add(self, *m):
        self.mobs.extend(m)
        return self

    def __iter__(self):
        return iter(self.mobs)

    def __getitem__(self, i):
        return self.mobs[i]

    def __len__(self):
        return len(self.mobs)

    def flat(self):
        for m in self.mobs:
            if isinstance(m, Group):
                yield from m.flat()
            else:
                yield m

    def bbox(self):
        bbs = [m.bbox() for m in self.flat() if m.bbox()]
        if not bbs:
            return None
        return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))

    def draw(self, frame):
        for m in sorted(self.mobs, key=lambda m: m.z):
            o0, f0 = m.opacity, m.offset
            m.opacity = o0 * self.opacity
            m.offset = (f0[0] + self.offset[0], f0[1] + self.offset[1])
            m.draw(frame)
            m.opacity, m.offset = o0, f0


class MathRow(Group):
    """A left-to-right math expression built from tokens.

    Tokens are strings; the special token "[]" draws an empty box, "[7]" a box with 7 in it.
    Math always reads left-to-right, even inside Hebrew content.
        MathRow(["5", "×", "[]", "=", "4", "×", "[]", "+", "7"], center=(960, 300))
    """

    def __init__(self, tokens, center=(W / 2, H / 2), size=72, color=WHITE, gap=None,
                 box_color=YELLOW, colors: dict | None = None, weight=500):
        super().__init__()
        self.layout_check = False
        gap = gap if gap is not None else size * 0.28
        colors = colors or {}
        items, widths = [], []
        for i, tok in enumerate(tokens):
            col = colors.get(i, color)
            if tok.startswith("[") and tok.endswith("]"):
                bs = size * 0.95
                widths.append(bs)
                items.append(("box", tok[1:-1], col if i in colors else box_color, bs))
            else:
                t = Text(tok, size=size, color=col, weight=weight)
                widths.append(t.width)
                items.append(("text", t, col, t.width))
        total = sum(widths) + gap * (len(widths) - 1)
        x = center[0] - total / 2
        self.slots = []
        for (kind, obj, col, w) in items:
            cx = x + w / 2
            if kind == "box":
                box = Rect((cx, center[1]), w, w, stroke=col, stroke_width=5, fill=col, fill_opacity=0.12)
                g = Group(box)
                if obj:
                    g.add(Text(obj, (cx, center[1]), size=int(size * 0.8), color=col, weight=700))
                self.add(g)
                self.slots.append(g)
            else:
                obj.pos = (cx, center[1])
                self.add(obj)
                self.slots.append(obj)
            x += w + gap
        self.center_pos = center


class Axes(Group):
    """2-D axes mapping math coords to pixels. axes.p(x, y) -> pixel point."""

    def __init__(self, x_range=(-4, 4), y_range=(-3, 5), origin_px=None, unit=None,
                 box=(260, 150, 1660, 900), color=GREY, ticks=True, tick_size=26):
        super().__init__()
        self.layout_check = False
        x0, y0, x1, y1 = box
        self.xr, self.yr = x_range, y_range
        sx = (x1 - x0) / (x_range[1] - x_range[0])
        sy = (y1 - y0) / (y_range[1] - y_range[0])
        self.ux = self.uy = unit or min(sx, sy)
        w = self.ux * (x_range[1] - x_range[0]); h = self.uy * (y_range[1] - y_range[0])
        self.left = (x0 + x1) / 2 - w / 2
        self.top = (y0 + y1) / 2 - h / 2
        self.add(Arrow(self.p(x_range[0], 0), self.p(x_range[1] + 0.3, 0), color=color, width=3, head=16))
        self.add(Arrow(self.p(0, y_range[0]), self.p(0, y_range[1] + 0.3), color=color, width=3, head=16))
        if ticks:
            for k in range(math.ceil(x_range[0]), math.floor(x_range[1]) + 1):
                if k == 0:
                    continue
                px, py = self.p(k, 0)
                self.add(Line((px, py - 8), (px, py + 8), color=color, width=2))
                self.add(Text(str(k), (px, py + 30), size=tick_size, color=color))
            for k in range(math.ceil(y_range[0]), math.floor(y_range[1]) + 1):
                if k == 0:
                    continue
                px, py = self.p(0, k)
                self.add(Line((px - 8, py), (px + 8, py), color=color, width=2))
                self.add(Text(str(k), (px - 30, py), size=tick_size, color=color, anchor="rm"))

    def p(self, x, y):
        return (self.left + (x - self.xr[0]) * self.ux, self.top + (self.yr[1] - y) * self.uy)

    def graph_points(self, f, x_min=None, x_max=None, n=240, clip=True):
        x_min = self.xr[0] if x_min is None else x_min
        x_max = self.xr[1] if x_max is None else x_max
        pts = []
        for i in range(n + 1):
            x = x_min + (x_max - x_min) * i / n
            y = f(x)
            if clip:
                y = max(min(y, self.yr[1] + 0.25), self.yr[0] - 0.25)
            pts.append(self.p(x, y))
        return np.array(pts)

    def plot(self, f, color=BLUE, width=6, **kw):
        return Polyline(self.graph_points(f, **{k: v for k, v in kw.items() if k in ("x_min", "x_max", "n")}),
                        color=color, width=width)


# --------------------------------------------------------------------------------------
# Animations
# --------------------------------------------------------------------------------------
class Anim:
    remover = False
    mob: Mob | None = None

    def begin(self, scene: "Scene"):
        pass

    def update(self, a: float):
        pass

    def finish(self, scene: "Scene"):
        self.update(1.0)


def _targets(m: Mob):
    return list(m.flat()) if isinstance(m, Group) else [m]


class FadeIn(Anim):
    def __init__(self, mob, shift=(0, 0), scale=1.0):
        self.mob, self.shift, self.s0 = mob, shift, scale

    def begin(self, scene):
        self.target_opacity = self.mob.opacity if self.mob.opacity > 0 else 1.0
        self.mob.opacity = 0
        scene.add(self.mob)

    def update(self, a):
        self.mob.opacity = self.target_opacity * a
        self.mob.offset = (-self.shift[0] * (1 - a), -self.shift[1] * (1 - a))
        if self.s0 != 1.0:
            self.mob.scale = lerp(self.s0, 1.0, a)


class FadeOut(Anim):
    remover = True

    def __init__(self, mob, shift=(0, 0)):
        self.mob, self.shift = mob, shift

    def begin(self, scene):
        self.o0 = self.mob.opacity

    def update(self, a):
        self.mob.opacity = self.o0 * (1 - a)
        self.mob.offset = (self.shift[0] * a, self.shift[1] * a)

    def finish(self, scene):
        self.update(1.0)
        scene.remove(self.mob)
        self.mob.opacity, self.mob.offset = self.o0, (0, 0)


class Create(Anim):
    """Draws outlines progressively, then fades fill in. Works on Shape or Group."""

    def __init__(self, mob):
        self.mob = mob

    def begin(self, scene):
        scene.add(self.mob)
        for m in _targets(self.mob):
            if isinstance(m, Shape):
                m.progress, m.fill_progress = 0.0, 0.0
            elif isinstance(m, Text):
                m.reveal = 0.0

    def update(self, a):
        for m in _targets(self.mob):
            if isinstance(m, Shape):
                m.progress = min(1.0, a / 0.7)
                m.fill_progress = max(0.0, (a - 0.45) / 0.55)
            elif isinstance(m, Text):
                m.reveal = a


class Write(Anim):
    """Wipes text in reading direction (right-to-left for Hebrew)."""

    def __init__(self, mob):
        self.mob = mob

    def begin(self, scene):
        scene.add(self.mob)
        for m in _targets(self.mob):
            if isinstance(m, Text):
                m.reveal = 0.0
            elif isinstance(m, Shape):
                m.progress = m.fill_progress = 0.0

    def update(self, a):
        for m in _targets(self.mob):
            if isinstance(m, Text):
                m.reveal = a
            elif isinstance(m, Shape):
                m.progress = a; m.fill_progress = a


class Tween(Anim):
    """Interpolate attributes: Tween(mob, opacity=0.3, pos=(100,200), points=new_pts, fill=RED)."""

    def __init__(self, mob, **targets):
        self.mob, self.targets = mob, targets

    def begin(self, scene):
        self.start = {}
        for k, v in self.targets.items():
            cur = getattr(self.mob, k)
            self.start[k] = np.array(cur, dtype=float) if isinstance(cur, np.ndarray) else cur

    def update(self, a):
        for k, end in self.targets.items():
            s = self.start[k]
            if isinstance(s, np.ndarray):
                setattr(self.mob, k, s + (np.asarray(end, float) - s) * a)
            elif isinstance(s, tuple):
                v = lerp(s, tuple(end), a)
                if k in ("fill", "stroke", "color"):
                    v = tuple(int(round(x)) for x in v)
                    if isinstance(self.mob, Text):
                        self.mob.color = v
                        continue
                setattr(self.mob, k, v)
            else:
                setattr(self.mob, k, lerp(s, end, a))


def Morph(shape: Shape, points):
    return Tween(shape, points=np.asarray(points, float))


class MoveTo(Anim):
    """Move a Mob (or Group) so its bbox centre lands on target (via offset-free translation)."""

    def __init__(self, mob, target):
        self.mob, self.target = mob, np.array(target, float)

    def begin(self, scene):
        bb = self.mob.bbox()
        self.delta = self.target - np.array([(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2])
        self.items = []
        for m in _targets(self.mob):
            if isinstance(m, Shape):
                self.items.append((m, "points", m.points.copy()))
            elif isinstance(m, Text):
                self.items.append((m, "pos", np.array(m.pos, float)))

    def update(self, a):
        for m, attr, s in self.items:
            v = s + self.delta * a
            setattr(m, attr, v if attr == "points" else (float(v[0]), float(v[1])))


class Indicate(Anim):
    """Pulse scale up and back, optional colour flash."""

    def __init__(self, mob, scale=1.12):
        self.mob, self.s = mob, scale

    def update(self, a):
        k = math.sin(math.pi * a)
        for m in _targets(self.mob):
            m.scale = 1 + (self.s - 1) * k


class Func(Anim):
    """Custom: Func(lambda a: ...) called with eased alpha each frame."""

    def __init__(self, fn, mob=None):
        self.fn, self.mob = fn, mob

    def update(self, a):
        self.fn(a)


class Lagged(Anim):
    """Run several animations with staggered starts. lag in 0..1 of total."""

    def __init__(self, *anims, lag=0.25):
        self.anims, self.lag = anims, lag

    def begin(self, scene):
        for an in self.anims:
            an.begin(scene)
        n = len(self.anims)
        self.span = 1.0 / (1 + self.lag * (n - 1)) if n > 1 else 1.0

    def update(self, a):
        for i, an in enumerate(self.anims):
            start = i * self.lag * self.span
            an.update(smooth((a - start) / self.span) if self.span > 0 else 1)

    def finish(self, scene):
        for an in self.anims:
            an.finish(scene)


# --------------------------------------------------------------------------------------
# Scene
# --------------------------------------------------------------------------------------
class Scene:
    def __init__(self, name: str, out_dir: str = ".", width=W, height=H, fps=FPS, bg=BG,
                 quality: str | None = None):
        q = quality or os.environ.get("MATHVIZ_QUALITY", "h")
        self.scale_out = {"l": 0.5, "m": 2 / 3, "h": 1.0}.get(q, 1.0)
        self.name, self.out_dir, self.fps, self.bg = name, out_dir, fps, bg
        self.w, self.h = width, height
        self.mobs: list[Mob] = []
        self.issues = 0
        self._seen = set()
        self.time = 0.0
        self._title = None
        self._cap = None
        self._cap_bg = None
        self.preview_only = os.environ.get("MATHVIZ_PREVIEW") == "1"
        self.snap_dir = os.environ.get("MATHVIZ_SNAP_DIR")
        self._snap_i = 0
        os.makedirs(out_dir, exist_ok=True)
        self.out_path = os.path.join(out_dir, f"{name}.mp4")
        self._bgframe = np.empty((height, width, 3), np.uint8); self._bgframe[:] = bg
        self._proc = None
        if not self.preview_only:
            ow, oh = int(width * self.scale_out) // 2 * 2, int(height * self.scale_out) // 2 * 2
            vf = [] if self.scale_out == 1.0 else ["-vf", f"scale={ow}:{oh}:flags=area"]
            self._proc = subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", *vf,
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", self.out_path], stdin=subprocess.PIPE)

    # scene graph ------------------------------------------------------------------------
    def add(self, *mobs):
        for m in mobs:
            if m not in self.mobs:
                self.mobs.append(m)
        return mobs[0] if len(mobs) == 1 else mobs

    def remove(self, *mobs):
        for m in mobs:
            if m in self.mobs:
                self.mobs.remove(m)

    def render_frame(self) -> np.ndarray:
        f = self._bgframe.copy()
        for m in sorted(self.mobs, key=lambda m: m.z):
            m.draw(f)
        return f

    def _emit(self, frame, count=1):
        self.time += count / self.fps
        if self._proc is None:
            return
        b = frame.tobytes()
        for _ in range(count):
            self._proc.stdin.write(b)

    # timeline ---------------------------------------------------------------------------
    def play(self, *anims, run_time: float = 1.0, ease=smooth):
        anims = [a for a in anims if a is not None]
        for an in anims:
            an.begin(self)
        n = max(1, int(round(run_time * self.fps)))
        if self.preview_only:
            for an in anims:
                an.update(1.0)
            self.time += n / self.fps
        else:
            for i in range(n):
                a = ease((i + 1) / n)
                for an in anims:
                    an.update(a)
                self._emit(self.render_frame())
        for an in anims:
            an.finish(self)
        self._check_layout()

    def wait(self, t: float = 1.0):
        n = max(1, int(round(t * self.fps)))
        self._check_layout()
        if self.preview_only:
            self.time += n / self.fps
            self._maybe_snap()
            return
        self._emit(self.render_frame(), n)
        self._maybe_snap()

    def _maybe_snap(self):
        if self.snap_dir:
            os.makedirs(self.snap_dir, exist_ok=True)
            self._snap_i += 1
            self.snapshot(os.path.join(self.snap_dir, f"{self.name}_{self._snap_i:03d}.png"))

    def snapshot(self, path: str):
        Image.fromarray(self.render_frame()).save(path)
        return path

    # guard rails ------------------------------------------------------------------------
    def _check_layout(self):
        texts = []
        for m in self.mobs:
            for leaf in (m.flat() if isinstance(m, Group) else [m]):
                if not leaf.layout_check or leaf.opacity <= 0.05:
                    continue
                bb = leaf.bbox()
                if not bb:
                    continue
                label = getattr(leaf, "text", type(leaf).__name__)
                if bb[0] < SAFE - 2 or bb[1] < SAFE - 2 or bb[2] > self.w - SAFE + 2 or bb[3] > self.h - SAFE + 2:
                    self._warn(("out", label, tuple(int(v) for v in bb)),
                               f"out of safe area: {label!r} bbox={tuple(int(v) for v in bb)}")
                if isinstance(leaf, Text):
                    texts.append((label, bb))
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i][1], texts[j][1]
                ix = min(a[2], b[2]) - max(a[0], b[0]); iy = min(a[3], b[3]) - max(a[1], b[1])
                if ix > 4 and iy > 4:
                    self._warn(("ov", texts[i][0], texts[j][0]),
                               f"text overlap: {texts[i][0]!r} <> {texts[j][0]!r}")

    def _warn(self, key, msg):
        if key in self._seen:
            return
        self._seen.add(key)
        self.issues += 1
        print(f"[layout] WARN t={self.time:5.1f}s {msg}", file=sys.stderr)

    # conveniences -----------------------------------------------------------------------
    def title(self, text, size=60, color=WHITE, run_time=0.9):
        new = Text(text, (self.w / 2, 100), size=size, color=color, weight=700, max_width=self.w - 2 * SAFE - 40)
        anims = [Write(new)]
        if self._title is not None:
            anims.append(FadeOut(self._title, shift=(0, -20)))
        self.play(*anims, run_time=run_time)
        self._title = new
        return new

    def caption(self, text, wait: float | None = None, size=44, color=WHITE, run_time=0.6):
        """Bottom subtitle with a dark backing plate. Replaces the previous caption.
        If wait is None, waits long enough to read it (~ 0.075s per character, min 1.8s)."""
        y = self.h - 110
        new = Text(text, (self.w / 2, y), size=size, color=color, max_width=self.w - 2 * SAFE - 80)
        plate = RoundRect((self.w / 2, y), new.width + 70, new.height + 44, r=22,
                          fill=(8, 11, 15), fill_opacity=0.82, stroke=None, z=9)
        plate.layout_check = False
        anims = [FadeIn(plate, shift=(0, 12)), FadeIn(new, shift=(0, 12))]
        if self._cap is not None:
            anims += [FadeOut(self._cap, shift=(0, -12)), FadeOut(self._cap_bg, shift=(0, -12))]
        self.play(*anims, run_time=run_time)
        self._cap, self._cap_bg = new, plate
        self.wait(wait if wait is not None else max(1.8, 0.075 * len(text)))
        return new

    def clear_caption(self, run_time=0.4):
        if self._cap is not None:
            self.play(FadeOut(self._cap), FadeOut(self._cap_bg), run_time=run_time)
            self._cap = self._cap_bg = None

    def clear_screen(self, keep=(), run_time=0.6):
        """Fade out everything except the title and anything in keep."""
        keep = set(keep) | {self._title}
        outs = [FadeOut(m) for m in self.mobs if m not in keep and m is not self._cap and m is not self._cap_bg]
        if self._cap is not None:
            outs += [FadeOut(self._cap), FadeOut(self._cap_bg)]
            self._cap = self._cap_bg = None
        if outs:
            self.play(*outs, run_time=run_time)

    def close(self):
        if self._proc is not None:
            self._proc.stdin.close()
            self._proc.wait()
        status = "DONE" if self.issues == 0 else "DONE (fix before delivery!)"
        print(f"[layout] {status} found {self.issues} layout issues — {self.name}, {self.time:.1f}s")
        if self._proc is not None:
            print(f"[render] video: {os.path.abspath(self.out_path)}")
        return self.out_path


__all__ = [n for n in dir() if not n.startswith("_")]
