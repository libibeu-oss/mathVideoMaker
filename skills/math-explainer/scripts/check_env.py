#!/usr/bin/env python3
"""环境体检：确认 manim / ffmpeg 可用，报告 LaTeX 是否可用。

用法:
    python3 check_env.py

退出码 0 = 视频渲染所需的核心组件齐全（manim + ffmpeg）。
LaTeX 不是硬性要求；缺它时改用 Text 写公式即可。
"""
import os
import shutil
import sys

# 若存在 setup_manim.sh 创建的 venv，且当前不是用它在跑，则自动切换到 venv 的解释器，
# 这样 import manim 才能命中安装位置（否则系统 python 会误报“未装 manim”）。
_VENV = os.environ.get("MANIM_VENV", os.path.expanduser("~/.cache/manim-explainer-venv"))
_VENV_PY = os.path.join(_VENV, "bin", "python")
if (
    os.path.exists(_VENV_PY)
    and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PY)
    and os.environ.get("_MANIM_CHECK_REEXEC") != "1"
):
    os.environ["_MANIM_CHECK_REEXEC"] = "1"
    os.execv(_VENV_PY, [_VENV_PY, os.path.abspath(__file__)])

GREEN, RED, YEL, RST = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def line(tag_color, tag, msg):
    print(f"{tag_color}[{tag}]{RST} {msg}")


def main() -> int:
    core_ok = True

    # manim
    have_manim = True
    try:
        import manim  # noqa
        line(GREEN, " ok ", f"manim {manim.__version__}")
    except Exception as e:  # noqa
        have_manim = False
        line(YEL, "warn", f"manim not importable ({e}) -> checking the mathviz_lite fallback engine")

    # mathviz_lite fallback (numpy + Pillow/raqm + opencv + ffmpeg) — works where PyPI is blocked
    have_lite = True
    for mod in ("numpy", "PIL", "cv2"):
        try:
            __import__(mod)
        except Exception:
            have_lite = False
            line(RED if not have_manim else YEL, "miss", f"python module {mod} (needed by mathviz_lite)")
    try:
        from PIL import features
        if features.check("raqm"):
            line(GREEN, " ok ", "Pillow has raqm -> right-to-left text (Hebrew/Arabic) renders correctly")
        else:
            line(YEL, "warn", "Pillow without raqm -> Hebrew/Arabic text may render reversed")
    except Exception:
        pass
    if not have_manim and not have_lite:
        core_ok = False
        line(RED, "FAIL", "neither manim nor the mathviz_lite dependencies are available")
        line(YEL, "fix ", "run setup_manim.sh, or pip install numpy pillow opencv-python")

    # ffmpeg
    if shutil.which("ffmpeg"):
        line(GREEN, " ok ", "ffmpeg 已安装")
    else:
        core_ok = False
        line(RED, "FAIL", "未找到 ffmpeg（合成视频必需）")
        line(YEL, "fix ", "mac: brew install ffmpeg ; linux: apt-get install ffmpeg")

    # LaTeX（可选）
    if shutil.which("latex"):
        line(GREEN, " ok ", "LaTeX 可用 → 可以使用 MathTex / Tex")
    else:
        line(YEL, "warn", "未找到 LaTeX（可选）→ 公式请用 Text + Unicode（见 manim-guide）")

    # 中文字体提示（仅 macOS 常见字体探测，非强制）
    print()
    print("中文字体提示：Text 显示中文需指定支持中文的字体，例如 mac 上 font=\"PingFang SC\"。")

    print()
    if core_ok:
        engine = "manim" if have_manim else "lite"
        line(GREEN, "PASS", f"ready to render. ENGINE={engine}"
             + ("" if have_manim else "  (use templates/mathviz_lite.py + scene_lite_template.py)"))
        return 0
    line(RED, "STOP", "核心环境不完整，先修复上面的 FAIL 再继续。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
