"""כמה שווה הקופסה? 5 × □ = 4 × □ + 7 — פתרון במאזניים (כיתות ג׳–ה׳).

Render:  python3 scene.py            (MATHVIZ_QUALITY=l|m|h, default h = 1080p)
Output:  ./BoxEquation.mp4
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "skills", "math-explainer", "templates"))
from mathviz_lite import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- shared design (same values as index.html) -----------------------------------------
LEFT_BOXES, RIGHT_BOXES, UNITS, ANSWER = 5, 4, 7, 7
BOX_COL, UNIT_COL, BEAM_COL = YELLOW, TEAL, GREY

PIVOT = np.array([960.0, 470.0])
HALF = 410.0          # half beam length
HANG = 190.0          # pan distance below beam end
PAN_W = 360.0
BOX = 60.0
UNIT = 34.0


class Item:
    def __init__(self, kind, side, row, col, ncols):
        self.kind, self.side, self.row, self.col, self.ncols = kind, side, row, col, ncols
        self.opacity, self.lift, self.label = 1.0, 0.0, "?"


class Balance(Mob):
    """Pan balance whose contents follow the tilt. angle > 0 => right side goes down."""
    z = 1
    layout_check = True

    def __init__(self):
        super().__init__()
        self.angle = 0.0
        self.items: list[Item] = []
        self._txt = {}
        for i in range(LEFT_BOXES):
            self.items.append(Item("box", "L", 0, i, LEFT_BOXES))
        for i in range(RIGHT_BOXES):
            self.items.append(Item("box", "R", 0, i, RIGHT_BOXES))
        for i in range(UNITS):
            self.items.append(Item("unit", "R", 1, i, UNITS))

    def boxes(self, side):
        return [it for it in self.items if it.kind == "box" and it.side == side]

    def pan_center(self, side):
        d = np.array([math.cos(self.angle), math.sin(self.angle)]) * HALF
        end = PIVOT - d if side == "L" else PIVOT + d
        return end, end + np.array([0, HANG])

    def bbox(self):
        _, pl = self.pan_center("L"); _, pr = self.pan_center("R")
        return (pl[0] - PAN_W / 2 - 10, 360, pr[0] + PAN_W / 2 + 10, 860)

    def _label(self, s):
        if s not in self._txt:
            self._txt[s] = Text(s, size=40, color=BG, weight=700)
        return self._txt[s]

    def draw(self, frame):
        o = self.opacity
        # stand
        base = Polygon([(PIVOT[0] - 120, 860), (PIVOT[0] + 120, 860), (PIVOT[0], 790)],
                       fill=DIM, fill_opacity=1, stroke=None)
        pole = Line((PIVOT[0], 800), PIVOT, color=BEAM_COL, width=10)
        for m in (base, pole):
            m.opacity = o; m.draw(frame)
        endL, panL = self.pan_center("L")
        endR, panR = self.pan_center("R")
        for end, pan in ((endL, panL), (endR, panR)):
            for dx in (-PAN_W / 2 + 20, PAN_W / 2 - 20):
                s = Line(end, pan + [dx, 0], color=DIM, width=3); s.opacity = o; s.draw(frame)
            p = Shape([pan + [-PAN_W / 2, 0], pan + [PAN_W / 2, 0], pan + [PAN_W / 2 - 30, 22], pan + [-PAN_W / 2 + 30, 22]],
                      fill=BEAM_COL, fill_opacity=1, stroke=None)
            p.opacity = o; p.draw(frame)
        beam = Line(endL, endR, color=WHITE, width=12); beam.opacity = o; beam.draw(frame)
        hub = Circle(PIVOT, 14, fill=WHITE, fill_opacity=1, stroke=None); hub.opacity = o; hub.draw(frame)
        # contents
        for it in sorted(self.items, key=lambda it: it.lift > 0):   # lifted boxes on top
            if it.opacity <= 0.01:
                continue
            pan = panL if it.side == "L" else panR
            size = BOX if it.kind == "box" else UNIT
            gap = 8 if it.kind == "box" else 6
            roww = it.ncols * size + (it.ncols - 1) * gap
            cx = pan[0] - roww / 2 + size / 2 + it.col * (size + gap)
            cy = pan[1] - size / 2 - (0 if it.row == 0 else BOX + 8) - it.lift
            if it.kind == "box":
                r = Rect((cx, cy), size, size, fill=BOX_COL, fill_opacity=0.95, stroke=WHITE, stroke_width=3)
                r.opacity = o * it.opacity; r.draw(frame)
                t = self._label(it.label); t.pos = (cx, cy); t.opacity = o * it.opacity; t.draw(frame)
            else:
                r = Rect((cx, cy), size, size, fill=UNIT_COL, fill_opacity=0.95, stroke=WHITE, stroke_width=2)
                r.opacity = o * it.opacity; r.draw(frame)


def eq_row(tokens, colors=None):
    return MathRow(tokens, center=(960, 235), size=76, colors=colors)


def main():
    s = Scene("BoxEquation", out_dir=HERE)

    # ---------- 1. the question --------------------------------------------------------
    s.title("כמה שווה הקופסה?")
    eq = eq_row(["5", "×", "[]", "=", "4", "×", "[]", "+", "7"])
    s.play(FadeIn(eq, shift=(0, 16)), run_time=0.9)
    s.caption("בשתי הקופסאות מסתתר אותו מספר. איזה מספר זה?")

    # ---------- 2. picture it as a balance ---------------------------------------------
    bal = Balance()
    s.play(FadeIn(bal, shift=(0, 30)), run_time=1.2)
    s.caption("נדמיין מאזניים. משמאל: 5 קופסאות. מימין: 4 קופסאות ועוד 7 קוביות של 1.")
    s.caption("הסימן = אומר שהמאזניים מאוזנים: שני הצדדים שוקלים אותו דבר.")

    # ---------- 3. a guess that fails ----------------------------------------------------
    s.caption("ננסה לנחש: אולי בכל קופסה יש 5?", wait=0.6)
    for it in bal.boxes("L") + bal.boxes("R"):
        it.label = "5"
    s.wait(0.6)
    wl = Text("5 × 5 = 25", (560, 885), size=44, color=YELLOW, weight=700)
    wr = Text("4 × 5 + 7 = 27", (1360, 885), size=44, color=YELLOW, weight=700)
    s.play(FadeIn(wl), FadeIn(wr), run_time=0.6)
    s.play(Tween(bal, angle=0.13), run_time=1.0)
    s.caption("משמאל 25, מימין 27 — הצד הימני כבד יותר. הניחוש לא נכון.")
    s.play(FadeOut(wl), FadeOut(wr), Tween(bal, angle=0.0), run_time=0.9)
    for it in bal.boxes("L") + bal.boxes("R"):
        it.label = "?"
    s.caption("במקום לנחש — נחשוב.", wait=1.4)

    # ---------- 4. remove a box from BOTH sides, four times ------------------------------
    s.caption("כלל הזהב: אם מורידים קופסה אחת משני הצדדים, המאזניים נשארים מאוזנים.", wait=0.8)
    steps = [
        (["4", "×", "[]", "=", "3", "×", "[]", "+", "7"], 1.3),
        (["3", "×", "[]", "=", "2", "×", "[]", "+", "7"], 0.9),
        (["2", "×", "[]", "=", "1", "×", "[]", "+", "7"], 0.9),
        (["1", "×", "[]", "=", "7"], 1.1),
    ]
    for k, (tokens, rt) in enumerate(steps):
        l = bal.boxes("L")[-(k + 1)]
        r = bal.boxes("R")[-(k + 1)]

        def lift(a, l=l, r=r):
            for it in (l, r):
                it.lift = 120 * a
                it.opacity = 1 - a
        new = eq_row(tokens)
        s.play(Func(lift), FadeOut(eq, shift=(0, -14)), FadeIn(new, shift=(0, 14)), run_time=rt)
        eq = new
        s.wait(0.5 if k < 3 else 0.9)
        if k == 0:
            s.caption("הורדנו אחת מכל צד — עדיין מאוזן. נמשיך באותה דרך.", wait=2.4)

    s.caption("נשארה קופסה אחת משמאל, ו־7 קוביות מימין. הן שוקלות אותו דבר!")
    new = eq_row(["[]", "=", "7"], colors={2: YELLOW})
    s.play(FadeOut(eq), FadeIn(new, scale=0.8), run_time=0.8)
    eq = new
    s.wait(1.2)

    # ---------- 5. check in the original equation ---------------------------------------
    s.caption("בדיקה: נחזיר את כל הקופסאות, ובכל אחת נשים 7.", wait=0.6)
    for it in bal.items:
        if it.kind == "box":
            it.label = "7"

    def back(a):
        for it in bal.items:
            if it.kind == "box" and it.opacity < 1:
                it.opacity = a
                it.lift = 120 * (1 - a)
    orig = eq_row(["5", "×", "[7]", "=", "4", "×", "[7]", "+", "7"])
    s.play(Func(back), FadeOut(eq), FadeIn(orig), run_time=1.2)
    eq = orig
    wl = Text("5 × 7 = 35", (560, 885), size=44, color=GREEN, weight=700)
    wr = Text("4 × 7 + 7 = 35", (1360, 885), size=44, color=GREEN, weight=700)
    s.play(FadeIn(wl, shift=(0, 10)), FadeIn(wr, shift=(0, 10)), run_time=0.8)
    s.caption("משמאל 35, ומימין 28 + 7 = 35. מאוזן — התשובה נכונה!", wait=3.0)
    s.clear_screen()

    # ---------- 6. summary ------------------------------------------------------------
    big = MathRow(["[7]"], center=(960, 420), size=150)
    s.play(FadeIn(big, scale=0.6), run_time=0.9, ease=ease_out_back)
    lines = [
        Text("שוויון הוא כמו מאזניים מאוזנים.", (960, 610), size=52),
        Text("מה שעושים לצד אחד — עושים גם לצד השני.", (960, 700), size=52, color=YELLOW, weight=700),
    ]
    s.play(Lagged(*[FadeIn(t, shift=(0, 16)) for t in lines], lag=0.5), run_time=1.6)
    s.wait(3.5)
    s.close()


if __name__ == "__main__":
    main()
