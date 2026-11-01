---
name: video-studio
description: Video Studio v1 — edit videos with ffmpeg in this environment. Use when the user asks to cut, trim, join, resize (9:16 / 1:1 / 16:9), add music or voice-over, add subtitles (including Hebrew RTL), add a logo/watermark or text, change speed, compress, extract audio or frames, or prepare a video for Reels/TikTok/YouTube.
version: 1.0.0
---

# Video Studio v1

Edit videos with `ffmpeg`/`ffprobe` (already installed). Work on copies; never overwrite the user's source file.

## Workflow
1. Inspect: `ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact "$IN"`
2. Plan the edit in one short list and do it — don't ask for confirmation of routine steps.
3. Output to `out/` with a descriptive name; default H.264 + AAC, `-pix_fmt yuv420p -movflags +faststart` so it plays everywhere.
4. Verify: ffprobe the output, and grab a frame (`-ss 1 -frames:v 1 check.jpg`) and look at it before reporting.

## Recipes
- **Trim** (precise): `ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c:v libx264 -crf 20 -c:a aac out.mp4`
- **Join clips** (same format): list file `file 'a.mp4'` lines → `ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4`. Different formats: scale/fps each first or use the `concat` filter.
- **Vertical 9:16 (1080×1920)** crop center: `-vf "scale=-2:1920,crop=1080:1920"`; with blurred background:
  `-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"`
- **Square 1:1**: `-vf "crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080"`
- **Background music** (ducked under speech): `-i music.mp3 -filter_complex "[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy`
- **Replace audio**: `-i voice.mp3 -map 0:v -map 1:a -c:v copy -shortest`
- **Normalize loudness** (social, -14 LUFS): `-af loudnorm=I=-14:TP=-1.5:LRA=11`
- **Subtitles burned in**: write `subs.srt`, then `-vf "subtitles=subs.srt:force_style='FontName=Noto Sans Hebrew,FontSize=18,Outline=2,Alignment=2'"`. For Hebrew make sure a Hebrew font is installed (`fc-list | grep -i hebrew`; else `apt-get install -y fonts-noto`). libass handles RTL shaping.
- **Text overlay**: `-vf "drawtext=fontfile=/path/font.ttf:text='שלום':fontsize=64:fontcolor=white:borderw=3:x=(w-tw)/2:y=h-200"` (Hebrew: prefer the subtitles/ASS route for correct RTL).
- **Logo watermark**: `-i logo.png -filter_complex "[1]scale=180:-1[l];[0][l]overlay=W-w-40:40"`
- **Fade in/out**: `-vf "fade=in:0:15,fade=out:st=DUR-0.5:d=0.5" -af "afade=in:d=0.5,afade=out:st=DUR-0.5:d=0.5"`
- **Speed**: 2× `-filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2[a]" -map "[v]" -map "[a]"`
- **Images → slideshow**: `ffmpeg -framerate 1/3 -i img%02d.jpg -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30" -pix_fmt yuv420p out.mp4`
- **Compress**: `-c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k` (H.265: `libx265 -crf 28 -tag:v hvc1`)
- **Extract audio**: `-vn -c:a libmp3lame -q:a 2 out.mp3`; **frames/thumbnail**: `-ss 3 -frames:v 1 thumb.jpg`
- **GIF**: `-vf "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"`

## Platform presets
| Target | Size | Max length | Notes |
|---|---|---|---|
| Reels / TikTok / Shorts | 1080×1920, 30fps | 90s / 10m / 60s | keep text out of top 220px and bottom 400px |
| Instagram feed | 1080×1350 or 1080×1080 | 60s | |
| YouTube | 1920×1080 | — | `-crf 18` |

## Heavier jobs
For motion graphics or programmatic video use the Remotion / motion-reel / animation-studio plugins if installed; for talking-head reels use it-reelsmaker; for audio cleanup use video-cleanup.

## Brand projects
- **WAWG** (event app, "לאן הולכים?"): always start from the WAWG brand kit — /home/user/wawg/brand-kit/WAWG-VIDEO-GUIDE.md, or the Google Drive folder "WAWG – חומרי וידאו" if the local copy is gone. Use the real logo, the real app screens (captured from WAWG-app-snapshot.html), the app's photos, Rubik, and the production pipeline in production/.

## Standing rule from the user
Never ask before fixing. When a check finds a glitch (leftover overlay, bad timing, contrast, audio level), fix it and re-render on your own, then report what changed. Always inspect frames around each scene cut and each tap/overlay end before delivering.
