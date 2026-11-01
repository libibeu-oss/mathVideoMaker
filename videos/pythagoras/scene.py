"""משפט פיתגורס — הוכחה בשיטת הסידור מחדש (שטחים).

Render:  python3 scene.py            (MATHVIZ_QUALITY=l|m|h, default h = 1080p)
Output:  ./Pythagoras.mp4
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
A, B = 3.0, 4.0              # legs a, b  (3-4-5 triangle)
L = A + B                    # big square side = a + b
SQ = 500                     # big square size in px
U = SQ / L
TRI = BLUE
COL_A, COL_B, COL_C = GREEN, ORANGE, YELLOW

ORIGIN_L = (540 - SQ / 2, 530 + SQ / 2)    # bottom-left corner of left square (pixels)
ORIGIN_R = (1380 - SQ / 2, 530 + SQ / 2)


def P(x, y, o):
    """math coords inside [0,L]^2 (y up) -> pixels."""
    return (o[0] + x * U, o[1] - y * U)


# triangles as (right-angle vertex, end of leg a, end of leg b) in math coords
LEFT_TRIS = [((L, 0), (B, 0), (L, B)), ((B, B), (L, B), (B, 0)),
             ((0, B), (0, L), (B, B)), ((B, L), (B, B), (0, L))]
RIGHT_TRIS = [((L, 0), (B, 0), (L, B)), ((L, L), (L, B), (A, L)),
              ((0, 0), (0, A), (B, 0)), ((0, L), (A, L), (0, A))]


def tri_shape(t, o, **kw):
    return Polygon([P(*v, o) for v in t], fill=TRI, fill_opacity=0.6, stroke=WHITE, stroke_width=3, **kw)


def rigid_path(src, dst):
    """Return f(alpha) -> 3 pixel points, moving triangle src->dst rigidly (rotate + slide)."""
    s = np.array(src, float); d = np.array(dst, float)
    ang = lambda T: math.atan2(*(T[1] - T[0])[::-1])
    a0, a1 = ang(s), ang(d)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    cs, cd = s.mean(axis=0), d.mean(axis=0)     # rotate about the centroid: compact path
    rel = s - cs

    def f(al):
        th = da * al
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        return cs + (cd - cs) * al + rel @ R.T
    return f


def main():
    s = Scene("Pythagoras", out_dir=HERE)

    # ---------- 1. the question --------------------------------------------------------
    s.title("משפט פיתגורס: למה a² + b² = c²?")
    k = 85
    p0, p1, p2 = np.array([760, 700]), np.array([760 + 4 * k, 700]), np.array([760, 700 - 3 * k])
    tri = Polygon([p0, p1, p2], fill=TRI, fill_opacity=0.45, stroke=WHITE, stroke_width=4)
    ra = RightAngleMark(p0, p1 - p0, p2 - p0)
    la = Text("a", (p0[0] - 40, (p0[1] + p2[1]) / 2), size=56, color=COL_A, weight=700)
    lb = Text("b", ((p0[0] + p1[0]) / 2, p0[1] + 45), size=56, color=COL_B, weight=700)
    lc = Text("c", ((p1[0] + p2[0]) / 2 + 30, (p1[1] + p2[1]) / 2 - 30), size=56, color=COL_C, weight=700)
    s.play(Create(tri), Create(ra), run_time=1.2)
    s.play(Write(la), Write(lb), Write(lc), run_time=0.8)
    s.caption("משולש ישר־זווית: הניצבים הם a ו־b, והיתר (הצלע הארוכה) הוא c.")
    s.caption("הטענה: a² + b² = c². לא נסתפק בזה — נראה בעיניים למה זה נכון.")
    s.clear_screen()

    # ---------- 2. two equal big squares -------------------------------------------------
    outL = Polygon([P(0, 0, ORIGIN_L), P(L, 0, ORIGIN_L), P(L, L, ORIGIN_L), P(0, L, ORIGIN_L)],
                   stroke=WHITE, stroke_width=5)
    outR = Polygon([P(0, 0, ORIGIN_R), P(L, 0, ORIGIN_R), P(L, L, ORIGIN_R), P(0, L, ORIGIN_R)],
                   stroke=WHITE, stroke_width=5)
    # side labels: bottom edge split into b + a
    labs = Group()
    for o in (ORIGIN_L, ORIGIN_R):
        y = o[1] + 38
        labs.add(Text("b", ((P(0, 0, o)[0] + P(B, 0, o)[0]) / 2, y), size=40, color=COL_B, weight=700))
        labs.add(Text("a", ((P(B, 0, o)[0] + P(L, 0, o)[0]) / 2, y), size=40, color=COL_A, weight=700))
        labs.add(Line((P(B, 0, o)[0], o[1] + 14), (P(B, 0, o)[0], o[1] + 60), color=GREY, width=3))
    s.play(Create(outL), Create(outR), run_time=1.2)
    s.play(FadeIn(labs, shift=(0, 10)), run_time=0.6)
    s.caption("נצייר שני ריבועים זהים, שצלע כל אחד מהם היא a + b. לכן השטחים שלהם שווים.")

    # ---------- 3. left arrangement -> a² and b² -----------------------------------------
    trisL = [tri_shape(t, ORIGIN_L) for t in LEFT_TRIS]
    s.play(Lagged(*[FadeIn(t, scale=0.6) for t in trisL], lag=0.35), run_time=1.6)
    sq_b = Polygon([P(0, 0, ORIGIN_L), P(B, 0, ORIGIN_L), P(B, B, ORIGIN_L), P(0, B, ORIGIN_L)],
                   fill=COL_B, fill_opacity=0.55, stroke=WHITE, stroke_width=3, z=-1)
    sq_a = Polygon([P(B, B, ORIGIN_L), P(L, B, ORIGIN_L), P(L, L, ORIGIN_L), P(B, L, ORIGIN_L)],
                   fill=COL_A, fill_opacity=0.55, stroke=WHITE, stroke_width=3, z=-1)
    t_b = Text("b²", P(B / 2, B / 2, ORIGIN_L), size=64, weight=700)
    t_a = Text("a²", P((B + L) / 2, (B + L) / 2, ORIGIN_L), size=56, weight=700)
    s.play(FadeIn(sq_b), FadeIn(sq_a), run_time=0.8)
    s.play(Write(t_b), Write(t_a), run_time=0.6)
    s.caption("בריבוע השמאלי נכניס 4 משולשים זהים. נשארים שני ריבועים: אחד בשטח a² ואחד בשטח b².")

    # ---------- 4. same 4 triangles, slid into the right square -> c² ---------------------
    copies, paths = [], []
    for src, dst in zip(LEFT_TRIS, RIGHT_TRIS):
        sp = np.array([P(*v, ORIGIN_L) for v in src]); dp = np.array([P(*v, ORIGIN_R) for v in dst])
        c = Polygon(sp, fill=TRI, fill_opacity=0.6, stroke=WHITE, stroke_width=3, z=2)
        copies.append(c); paths.append(rigid_path(sp, dp))
    s.add(*copies)

    def move(al):
        for c, f in zip(copies, paths):
            c.points = f(al)
    s.caption("עכשיו ניקח את אותם 4 משולשים בדיוק, ונזיז אותם לריבוע הימני — בסידור אחר.", wait=0.6)
    s.play(Func(move), run_time=3.2)
    sq_c = Polygon([P(B, 0, ORIGIN_R), P(L, B, ORIGIN_R), P(A, L, ORIGIN_R), P(0, A, ORIGIN_R)],
                   fill=COL_C, fill_opacity=0.5, stroke=WHITE, stroke_width=3, z=-1)
    t_c = Text("c²", P(L / 2, L / 2, ORIGIN_R), size=72, weight=700)
    edge = Line(P(B, 0, ORIGIN_R), P(L, B, ORIGIN_R), color=COL_C, width=9, z=3)
    t_ce = Text("c", ((P(B, 0, ORIGIN_R)[0] + P(L, B, ORIGIN_R)[0]) / 2 + 26,
                      (P(B, 0, ORIGIN_R)[1] + P(L, B, ORIGIN_R)[1]) / 2 + 26), size=42, color=COL_C, weight=700)
    s.play(FadeIn(sq_c), run_time=0.8)
    s.play(Create(edge), Write(t_ce), Write(t_c), run_time=0.9)
    s.caption("נשאר ריבוע אחד, מוטה. כל צלע שלו היא יתר של משולש — כלומר c. לכן שטחו c².")
    s.play(FadeOut(edge), FadeOut(t_ce), run_time=0.4)

    # ---------- 5. the key comparison ----------------------------------------------------
    s.caption("השוואה: שני הריבועים הגדולים שווים, ומשניהם הורדנו את אותם 4 משולשים.", wait=0.8)
    for t in trisL + copies:
        t.fill = TRI
    s.play(*[Tween(t, fill=(150, 190, 255)) for t in trisL + copies], run_time=0.5)
    s.play(*[Tween(t, fill=TRI, fill_opacity=0.18) for t in trisL + copies], run_time=0.9)
    s.wait(1.6)
    s.caption("לכן מה שנשאר חייב להיות שווה: השטח הירוק והכתום יחד שווה לשטח הצהוב.", wait=0.6)
    s.play(Indicate(Group(sq_a, sq_b, t_a, t_b), 1.06), Indicate(Group(sq_c, t_c), 1.06), run_time=1.4)
    eq = MathRow(["a²", "+", "b²", "=", "c²"], center=(960, 905), size=84,
                 colors={0: COL_A, 2: COL_B, 4: COL_C}, weight=700)
    s.clear_caption()
    s.play(FadeIn(eq, shift=(0, 20)), run_time=0.9)
    s.wait(2.4)
    s.clear_screen()

    # ---------- 6. summary + numeric check ---------------------------------------------
    steps = [
        "1. שני ריבועים גדולים זהים — צלע a + b",
        "2. מכל אחד מורידים 4 משולשים זהים",
        "3. מה שנשאר שווה: a² + b² = c²",
    ]
    rows = [Text(t, (1460, 300 + 95 * i), size=50, anchor="rm") for i, t in enumerate(steps)]
    s.play(Lagged(*[FadeIn(r, shift=(-30, 0)) for r in rows], lag=0.5), run_time=2.0)
    s.wait(1.5)
    big = Text("a² + b² = c²", (960, 640), size=110, color=COL_C, weight=700, glow=True)
    frame_box = RoundRect((960, 640), big.width + 90, big.height + 70, r=26, stroke=COL_C, stroke_width=5)
    s.play(Write(big), Create(frame_box), run_time=1.2)
    check = MathRow(["3²", "+", "4²", "=", "9", "+", "16", "=", "25", "=", "5²"], center=(960, 830),
                    size=58, colors={0: COL_A, 2: COL_B, 10: COL_C})
    s.caption("בדיקה עם מספרים: במשולש שניצביו 3 ו־4, היתר הוא 5.", wait=0.4)
    s.play(FadeIn(check, shift=(0, 16)), run_time=1.0)
    s.wait(3.5)
    s.close()


if __name__ == "__main__":
    main()
