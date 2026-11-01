
# WAWG video work
For any WAWG ad / video: use the brand kit at /home/user/wawg/brand-kit (guide: WAWG-VIDEO-GUIDE.md — logo, colors, Rubik font, real app snapshot + routes, app photos, script, production pipeline). A durable copy lives in the user's Google Drive folder "WAWG – חומרי וידאו" (id 1g9P17KRlGJlUlMhwJsqgXYeHHl-rsm8K): guide doc + capture.js, ad2.html, render.js, music.py, mux.sh. Logo + app snapshot are NOT in Drive (too large for the connector) — ask the user to re-send them. If the local folder is missing (new session), fetch it from Drive first.

# Working preference (user)
- Don't ask permission for fixes/re-renders. If something needs fixing (visual glitch, timing, quality issue), just fix it, re-render, and report what was fixed. Applies always, not only to WAWG.
- Before delivering any video, check frames around every scene transition and tap/overlay for leftover artifacts, and fix them before sending.

# WAWG voiceover
- Hebrew TTS: edge-tts (pip) through the proxy: `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt edge-tts --proxy "$HTTPS_PROXY" --voice he-IL-AvriNeural|he-IL-HilaNeural ...`. Needs speech.platform.bing.com in the environment's Allowed domains (user added it).
- Write WAWG as "וואג" and Neon Bloom as "ניאון בלום" in TTS text. Lines + voices: brand-kit/production/lines.tsv.
- Mix: mixvo.py places lines; duck.py lowers music 17 dB under speech (keep voice ≥11 dB above music); then loudnorm -14 LUFS.
- User said "תאשר תמיד" (always approve): save/commit Canva edits and similar tool confirmations without asking.
- User wants variety: don't reuse the same WAWG template/characters every time; try new concepts, people, looks (Canva generate-image works; ~2 concurrent jobs, export via a copied design + export-design).

# WAWG tools (added Nov 2026)
- Realistic footage: free Adobe Stock videos via Adobe connector (asset_search StockAsset pricing=free contentType=Video → asset_license_and_download_stock size 2160). Recipe + scripts: brand-kit/WAWG-VIDEO-GUIDE.md "Realistic footage spot" and brand-kit/production/real/ (green-screen phone composite of the real app = phone.py).
- User installed the Kling AI plugin + kling-ai-prompt-generator (AI video/image generation, uses user's Kling credits). Use them for AI shots; still composite the real logo/app screens ourselves.
- Canva generate-image credits ran out (Oct 31). Moda canvas_edit_image can generate/upscale images (metered).
- Always write "סביבכם" (not "סביבך") in WAWG scripts/captions/TTS.
