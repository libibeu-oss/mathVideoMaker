---
name: math-explainer
description: >-
  Turn a math or physics concept into a narrated-by-captions explainer VIDEO (MP4) plus a
  paired self-contained INTERACTIVE web page that share the same notation, parameters and
  colours. Use when the user asks to explain, teach, visualise or animate a formula,
  theorem, proof or word problem; asks for a "math video", "explainer video", "Manim
  animation", "interactive math demo", "סרטון הסבר במתמטיקה", "讲解视频" or similar.
  Works with Manim when it is installed, and otherwise with the bundled dependency-light
  engine (mathviz_lite: numpy + Pillow + opencv + ffmpeg), which also renders Hebrew and
  other right-to-left text correctly.
---

# Math Explainer — explainer video + interactive page

Turn one concept into **two complementary deliverables**:
- **Video (MP4)** — walks the viewer through *why* it is true, step by step.
- **Interactive page (single HTML file)** — the viewer drags the same parameters and sees the effect.

Make **both** unless the user explicitly asks for only one. They share one design: same
concept, notation, parameter ranges, palette and key visuals. The video explains; the page lets
people play.

> Follow the stages in order. Each stage says what to do, how, and how to check it. If unsure
> about an API, read the reference file — do not guess.

---

## 0. Rules that matter most

1. **Explain WHY, not just WHAT (hard rule).** The viewer must watch the result being derived.
   Derivation/argument is at least half of the video. Test: mute the captions — can you still
   follow the reasoning from the picture alone? See `references/pedagogy-and-storyboard.md` §0/§7.
2. **Storyboard before code.** No storyboard → no scene code (stage B).
3. **One idea per screen.** Fade out what the next step does not need. Nothing overlaps,
   nothing leaves the frame.
4. **Use the guard rails, then look.** Both engines print `[layout]` warnings (out of frame,
   text overlap) and must end with `0` issues. You can also *see* frames: save keyframes as PNG
   and open them with the Read tool before rendering the full video.
5. **Start from templates.** Copy from `templates/` instead of writing from scratch.
6. **Language follows the user.** Captions, titles and the page are written in the user's
   language. For Hebrew/Arabic use the lite engine (or a Manim font with RTL support) and keep
   math expressions left-to-right.
7. **Check before delivering.** MP4 exists and plays; the page passes `check_web.py`; you looked
   at keyframes of the video and a screenshot of the page.

---

## 1. Progress checklist (copy into your task list)

```
- [ ] A. Clarify the request (topic / audience / length / language) — default: video + page
- [ ] B. Storyboard <topic>/storyboard.md incl. the SHARED DESIGN SPEC
- [ ] C. Environment: run check_env.py → pick ENGINE (manim | lite)
- [ ] D1. Video: scene.py → keyframe preview → fix → full render → verify MP4
- [ ] D2. Page: index.html from the template → check_web.py → screenshot check
- [ ] E. Deliver both (+ storyboard), say which defaults you chose
```

Everything for one topic lives in one folder:
```
<topic-short-name>/
├── index.html      # interactive page (deliverable)
├── <Scene>.mp4     # video (deliverable)
├── storyboard.md   # storyboard + shared design spec
└── scene.py        # video source
```

---

## 2. Stage A — clarify

Use sensible defaults instead of asking many questions; state the defaults at delivery.

| Dimension | Default |
|-----------|---------|
| Topic | must be concrete (one theorem / one problem); narrow it if too broad |
| Form | **video + page** |
| Audience | middle/high school |
| Length | video 60–90 s |
| Language | the user's language |
| Style | dark background, high contrast |

---

## 3. Stage B — storyboard (the most important step)

Read `references/pedagogy-and-storyboard.md` (§0 red lines, §7 derivation strategies), copy
`templates/storyboard.md` to `<topic>/storyboard.md` and fill it:

- **Learning goal** — the one question the viewer can answer afterwards.
- **Shared design spec (required)** — notation; interactive parameters with range and step
  (page sliders; their key values become video shots); palette; key visuals.
- **Derivation line** — 3–6 atomic "because … therefore …" steps, ≥ half of the shots.
- **Shot list** — per shot: what is on screen, one caption line, transition.
- **Wrap-up** — one summary sentence + a held final frame.

Gate (rewrite if any fails): there is a real derivation; the picture alone carries the
reasoning; every step answers "why does this hold?"; the shared spec is written down.

---

## 4. Stage C — environment and engine choice

```bash
python3 ~/.claude/skills/math-explainer/scripts/check_env.py
```
(or `.claude/skills/...` when installed per project). It ends with `ENGINE=manim` or `ENGINE=lite`.

- **manim** — Manim Community is importable. Use `templates/scene_template.py` +
  `templates/mathviz.py` (SafeScene) and `scripts/render.sh`. If Manim is missing and you have
  internet + package access, `scripts/setup_manim.sh` installs it.
- **lite** — Manim is not available (common in sandboxes where PyPI is blocked). Use
  `templates/mathviz_lite.py` + `templates/scene_lite_template.py`. Needs only numpy, Pillow
  (with raqm for RTL), opencv-python and ffmpeg. Bundled font: `templates/fonts/Rubik[wght].ttf`
  (Latin + Hebrew; override with `MATHVIZ_FONT=/path/font.ttf`).

Do not spend long fighting a failed Manim install — switch to `lite`.

---

## 5. Stage D1 — the video

### Engine `lite` (mathviz_lite)

Canvas is 1920×1080 px, origin top-left, y down. Key API (read the module docstring for more):

| Need | Use |
|------|-----|
| Text (any language, RTL automatic) | `Text("...", pos, size, color, weight, anchor="mm"\|"rm"\|"lm", glow=)` |
| Math in reading order inside RTL text | automatic: math runs like `3² + 4² = 5²` are laid out left-to-right |
| Equation with boxes / coloured terms | `MathRow(["5","×","[]","=","[7]"], center, size, colors={i: COLOR})` |
| Shapes | `Polygon`, `Rect`, `RoundRect`, `Circle`, `Line`, `Polyline`, `Arrow`, `RightAngleMark`, `Group` |
| Graphs | `ax = Axes(x_range, y_range, box=(x0,y0,x1,y1))`, `ax.p(x,y)`, `ax.graph_points(f, x_min, x_max)` |
| Animations | `FadeIn(m, shift, scale)`, `FadeOut`, `Create`, `Write`, `Tween(m, attr=value)`, `Morph`, `MoveTo`, `Indicate`, `Lagged(*anims, lag)`, `Func(lambda a: ...)` |
| Timeline | `s.play(*anims, run_time, ease)`, `s.wait(t)` |
| Layout helpers | `s.title(text)`, `s.caption(text, wait=None)` (auto reading time, dark plate), `s.clear_caption()`, `s.clear_screen(keep=...)` |
| Custom drawing | subclass `Mob` and implement `draw(frame)` (see `videos/box-equation/scene.py`) |

Avoid glyphs the font lacks (the engine prints `[glyph] WARN`); draw such symbols as shapes —
e.g. an unknown box is `"[]"` in `MathRow`, not the character □.

Steps:
1. Copy `templates/scene_lite_template.py` → `<topic>/scene.py`; put the shared design values at the top.
2. Write the first two shots only, then **preview keyframes**:
   ```bash
   MATHVIZ_PREVIEW=1 MATHVIZ_SNAP_DIR=/tmp/snaps python3 <topic>/scene.py
   ```
   One PNG per `wait()`/`caption()`; no video is encoded, so it takes seconds. Combine them
   into a contact sheet and open it with Read. Fix overlaps, crowding, wrong text direction.
3. Finish all shots, preview again, then render:
   ```bash
   MATHVIZ_QUALITY=h python3 <topic>/scene.py      # h=1080p (default), m=720p, l=540p
   ```
4. The log must end with `[layout] DONE found 0 layout issues`. Extract 2–3 frames from the
   middle of animations (`ffmpeg -ss <t> -i video.mp4 -frames:v 1 f.png`) and look at them.

### Engine `manim`

Read `references/manim-guide.md` (API discipline, layout, old/new API table, troubleshooting)
and `references/manim-cookbook.md` (recipes). Copy `templates/scene_template.py` and
`templates/mathviz.py` into `<topic>/`, build with `SafeScene`, then:
```bash
python3 ~/.claude/skills/math-explainer/scripts/check_text.py <topic>/scene.py     # missing glyphs
bash    ~/.claude/skills/math-explainer/scripts/render.sh <topic>/scene.py SceneName s   # still + [layout]
bash    ~/.claude/skills/math-explainer/scripts/render.sh <topic>/scene.py SceneName h   # final 1080p
```
Gold-standard example of a real proof: `templates/example_pythagoras_proof.py`.
(The reference files are written in Chinese; the APIs and code are universal.)

**Video quality bar:** reasoning visible without captions; derivation ≥ 50 %; 0 layout issues;
no missing glyphs; captions stay long enough to read; final frame held.

---

## 6. Stage D2 — the interactive page

Read `references/interactive-web-guide.md`; copy `templates/interactive_template.html` to
`<topic>/index.html`.

- Same notation, ranges, palette as the video; every quantity the video changes becomes a slider
  (or buttons for discrete steps). Draw the same "mechanism marks" the video uses.
- Layout: single centred column (`.wrap`), interaction area first and modest in size (`.stage`,
  max-width ~420–560 px), explanation (`.explain`) below.
- **RTL pages** (Hebrew/Arabic): `<html lang="he" dir="rtl">`; wrap every inline math snippet in
  `<span class="m">` with `direction:ltr; unicode-bidi:isolate`; set `direction:ltr` on range
  inputs; canvas text uses `ctx.direction='ltr'` for math.
- Prefer plain HTML math (`a²`, `×`, `·`) for simple formulas so the page works offline; use
  KaTeX (CDN) only for formulas that really need it.
- Check:
  ```bash
  python3 ~/.claude/skills/math-explainer/scripts/check_web.py <topic>/index.html   # must be [PASS]
  ```
  If a headless browser is available (Playwright/Chrome), screenshot the page at a few slider
  values and look at them.

---

## 7. Stage E — deliver

- Send the MP4 and the HTML to the user (in Claude apps: `SendUserFile`; the page can also be
  published as an Artifact so it opens directly). Mention `storyboard.md`.
- How to use: watch the video first, then play with the page.
- Consistency: same concept, notation, parameter ranges, palette.
- Defaults used (audience, length, engine, language).
- One or two possible next steps (voice-over, another example, more presets).

---

## 8. Quick troubleshooting

| Symptom | Fix |
|---------|-----|
| `pip install manim` fails / no network | use ENGINE=lite |
| Hebrew letters in reverse order | Pillow lacks raqm → install a Pillow build with raqm, or use Manim with Pango |
| Math reversed inside a Hebrew sentence | lite engine handles it; in HTML wrap the math in `<span class="m">` |
| Boxes instead of characters | `[glyph] WARN` lists them → rephrase or draw as shape; set `MATHVIZ_FONT` |
| `[layout] WARN out of safe area` | move/shrink the object; captions sit at y≈970, titles at y≈100 |
| `[layout] WARN text overlap` | spread items, or `clear_screen()` between shots |
| Manim: `NameError: ShowCreation` | old API → `Create`; see manim-guide |
| Manim: LaTeX errors | no LaTeX installed → use `Text` instead of `MathTex` |

## Resources

- `references/pedagogy-and-storyboard.md` — how to explain clearly; storyboard method
- `references/manim-guide.md`, `references/manim-cookbook.md` — Manim API, layout, recipes
- `references/interactive-web-guide.md` — page structure, controls, canvas
- `templates/mathviz_lite.py` — dependency-light engine (RTL text, guard rails, preview snapshots)
- `templates/scene_lite_template.py` — scene skeleton for the lite engine
- `templates/fonts/` — Rubik variable font (OFL) for Latin + Hebrew
- `templates/mathviz.py`, `templates/scene_template.py`, `templates/example_pythagoras_proof.py` — Manim path
- `templates/interactive_template.html`, `templates/storyboard.md`
- `scripts/check_env.py` (picks the engine), `scripts/check_text.py`, `scripts/check_web.py`,
  `scripts/render.sh`, `scripts/setup_manim.sh`
- Finished examples in the repository: `videos/pythagoras`, `videos/box-equation`, `videos/parabola-n`
