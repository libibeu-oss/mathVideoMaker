"""הפרבולה y = n·x² — מה עושה המספר n? (חטיבה / תיכון)

Render:  python3 scene.py            (MATHVIZ_QUALITY=l|m|h, default h = 1080p)
Output:  ./ParabolaN.mp4
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "skills", "math-explainer", "templates"))
from mathviz_lite import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- shared design (same values as index.html) -----------------------------------------
X_RANGE, Y_RANGE = (-3, 3), (-3, 5)
BAR_XS = (-1.5, -1.0, 1.0, 1.5)
CURVE, BASE, BAR, MARK = BLUE, DIM, YELLOW, GREEN
PANEL_X = 1490


def curve_pts(ax, n):
    """Points of y = n·x², cut where the curve leaves the plot (no flat clipped tails)."""
    lim = Y_RANGE[1] + 0.2 if n > 0 else -Y_RANGE[0] + 0.2
    xm = X_RANGE[1] if abs(n) < 1e-9 else min(X_RANGE[1], (lim / abs(n)) ** 0.5)
    return ax.graph_points(lambda x: n * x * x, -xm, xm, clip=False)


def main():
    s = Scene("ParabolaN", out_dir=HERE)
    st = {"n": 1.0}

    # ---------- 1. the question + base parabola ----------------------------------------
    s.title("y = n·x²: מה עושה המספר n?")
    ax = Axes(X_RANGE, Y_RANGE, box=(200, 165, 1180, 890))
    s.play(FadeIn(ax), run_time=0.8)
    base = Polyline(curve_pts(ax, 1.0), color=BASE, width=5)
    base.z = -1
    curve = Polyline(curve_pts(ax, 1.0), color=CURVE, width=7)
    curve.z = 2
    s.play(Create(curve), run_time=1.4)
    eq = Text("y = n·x²", (PANEL_X, 330), size=88, weight=700)
    nval = Text("n = 1", (PANEL_X, 450), size=64, color=YELLOW, weight=700)
    s.play(Write(eq), FadeIn(nval), run_time=0.8)
    s.caption("נתחיל מ־n = 1, כלומר y = x². לכל x, גובה הנקודה על הגרף הוא x².")

    # ---------- 2. heights as bars -----------------------------------------------------
    bars, dots = [], []
    for x in BAR_XS:
        b = Line(ax.p(x, 0), ax.p(x, x * x), color=BAR, width=6, z=3)
        d = Circle(ax.p(x, x * x), 9, fill=BAR, fill_opacity=1, stroke=None, z=4)
        bars.append(b); dots.append(d)
    s.play(Lagged(*[Create(b) for b in bars], lag=0.2), Lagged(*[FadeIn(d) for d in dots], lag=0.2), run_time=1.2)
    s.caption("נסמן כמה גבהים: ב־x = 1 הגובה הוא 1, וב־x = 1.5 הגובה הוא 2.25.")

    mark = Circle(ax.p(1, 1), 14, fill=MARK, fill_opacity=1, stroke=WHITE, stroke_width=3, z=5)
    mlab = Text("(1, 1)", (ax.p(1, 1)[0] + 90, ax.p(1, 1)[1]), size=40, color=MARK, weight=700, z=5)

    def set_n(n):
        st["n"] = n
        curve.points = curve_pts(ax, n)
        for x, b, d in zip(BAR_XS, bars, dots):
            yv = max(min(n * x * x, Y_RANGE[1] + 0.25), Y_RANGE[0] - 0.25)
            b.points = np.array([ax.p(x, 0), ax.p(x, yv)])
            d.points = np.array(Circle(ax.p(x, yv), 9).points)
        mp = ax.p(1, n)
        mark.points = np.array(Circle(mp, 14).points)
        shown = f"{n:.1f}".rstrip("0").rstrip(".") if abs(n - round(n)) > 1e-6 else str(int(round(n)))
        if shown == "-0":
            shown = "0"
        shown = shown.replace("-", "−")
        nval.set_text(f"n = {shown}")
        mlab.set_text(f"(1, {shown})")
        mlab.pos = (mp[0] + 95, mp[1] - (30 if n >= 0 else -30))

    def animate_n(target, rt=2.0):
        n0 = st["n"]
        s.play(Func(lambda a: set_n(n0 + (target - n0) * a)), run_time=rt)

    # ---------- 3. multiply every height by n ------------------------------------------
    s.add(base)
    s.caption("עכשיו נכפול ב־n. המשמעות: כל גובה על הגרף מוכפל ב־n.", wait=1.0)
    animate_n(2.0, 2.4)
    s.caption("n = 2: כל גובה גדל פי 2. הפרבולה נמתחת למעלה — ולכן נראית צרה יותר.")
    s.play(FadeIn(mark, scale=0.4), FadeIn(mlab), run_time=0.6)
    s.caption("שימו לב לנקודה הירוקה: ב־x = 1 הגובה הוא בדיוק n. כך קוראים את n מהגרף.")

    # ---------- 4. 0 < n < 1 --------------------------------------------------------------
    animate_n(0.5, 2.2)
    s.caption("n = 0.5: כל גובה מתכווץ לחצי. הפרבולה נמוכה יותר — ולכן נראית רחבה יותר.")

    # ---------- 5. n = 0 -----------------------------------------------------------------
    animate_n(0.0, 1.8)
    s.caption("n = 0: כל הגבהים מוכפלים ב־0 ונעלמים. נשאר קו ישר: y = 0.")

    # ---------- 6. n < 0 -----------------------------------------------------------------
    animate_n(-1.0, 2.0)
    s.caption("n = −1: כל גובה מתהפך לשלילי. הפרבולה נפתחת כלפי מטה.")
    animate_n(1.0, 2.2)
    s.caption("ובחזרה ל־n = 1: אותה פרבולה מההתחלה.", wait=1.8)
    s.clear_screen()

    # ---------- 7. summary --------------------------------------------------------------
    rows = [
        ("n > 1 — צרה יותר (נמתחת למעלה)", WHITE),
        ("0 < n < 1 — רחבה יותר (מתכווצת)", WHITE),
        ("n = 0 — קו ישר, y = 0", WHITE),
        ("n < 0 — הפוכה, פתוחה כלפי מטה", WHITE),
    ]
    ts = [Text(t, (1400, 300 + 95 * i), size=52, color=c, anchor="rm") for i, (t, c) in enumerate(rows)]
    s.play(Lagged(*[FadeIn(t, shift=(-30, 0)) for t in ts], lag=0.4), run_time=2.2)
    s.wait(1.5)
    key = Text("כל גובה מוכפל ב־n", (960, 760), size=76, color=YELLOW, weight=700, glow=True)
    box = RoundRect((960, 760), key.width + 90, key.height + 70, r=26, stroke=YELLOW, stroke_width=5)
    s.play(Write(key), Create(box), run_time=1.2)
    s.wait(4.0)
    s.close()


if __name__ == "__main__":
    main()
