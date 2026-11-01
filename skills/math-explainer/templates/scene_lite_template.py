"""Scene skeleton for the mathviz_lite engine (no Manim needed).

Copy to <topic>/scene.py, keep the storyboard's shared design at the top, then fill the
shots. Every shot follows: build objects -> play() -> caption() -> clear_screen().

Preview keyframes (fast, no video, one PNG per wait/caption):
    MATHVIZ_PREVIEW=1 MATHVIZ_SNAP_DIR=/tmp/snaps python3 <topic>/scene.py
Render the video (h=1080p default, m=720p, l=540p):
    MATHVIZ_QUALITY=h python3 <topic>/scene.py        # -> <topic>/<Name>.mp4
The log must end with:  [layout] DONE found 0 layout issues
"""
import os
import sys

import numpy as np

# Point this at the skill's templates folder (or copy mathviz_lite.py + fonts/ next to scene.py)
SKILL_TEMPLATES = os.environ.get(
    "MATHVIZ_TEMPLATES", os.path.expanduser("~/.claude/skills/math-explainer/templates"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, SKILL_TEMPLATES)
from mathviz_lite import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- shared design (copy the same values into index.html) -------------------------------
MAIN, ACCENT = BLUE, YELLOW


def main():
    s = Scene("MathExplainer", out_dir=HERE)

    # 1. question ---------------------------------------------------------------------
    s.title("השאלה בשורה אחת")                 # any language; RTL handled automatically
    s.caption("משפט אחד שמציג את השאלה.")

    # 2. mechanism / intuition ---------------------------------------------------------
    sq = Rect((960, 520), 360, 360, fill=MAIN, fill_opacity=0.5, stroke=WHITE)
    s.play(Create(sq), run_time=1.2)
    s.caption("מה רואים — ולמה זה חשוב.")

    # 3. derivation: each step is one "because ... therefore ..." ---------------------
    eq = MathRow(["a²", "+", "b²", "=", "c²"], center=(960, 860), size=80,
                 colors={0: GREEN, 2: ORANGE, 4: YELLOW})
    s.play(FadeIn(eq, shift=(0, 20)), run_time=0.8)
    s.caption("צעד בהוכחה: כי ... לכן ...")
    s.clear_screen()

    # 4. wrap-up ------------------------------------------------------------------------
    big = Text("המסקנה", (960, 520), size=110, color=ACCENT, weight=700, glow=True)
    s.play(Write(big), run_time=1.0)
    s.wait(3)
    s.close()


if __name__ == "__main__":
    main()
