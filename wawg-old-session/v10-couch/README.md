# WAWG – "עוד ערב על הספה" (31 שניות, 9:16)

סרטון אנימציה של בעיה ופתרון: מבול של קבוצות, סטוריז שנעלמים ו"לינק?", ואז הספה. בדרופ עוברים לעולם של WAWG עם מסכי האפליקציה האמיתיים, ובסוף "בקרוב ב־App Store וב־Google Play".

- `ad10.html` – ציר הזמן. רינדור: `node render.js ad10.html video video.mp4 31` (עם `render.js` מ-brand-kit/production).
- מסכי האפליקציה: `node capture.js <WAWG-app-snapshot.html> cap` (‏capture.js מ-brand-kit/production).
- קריינות: `vo/lines.tsv`, הקול he-IL-HilaNeural ‏(edge-tts, ‏‎--rate=+6%‎).
- סאונד: `node sfxdump.js` ואז `python3 mix.py`. המוזיקה היא Cat Walk של Arulo (רישיון Mixkit חינמי לשימוש מסחרי), מנקודה 73.65 שניות כדי שהדרופ ייפול על שנייה 15. הקול 13–17 dB מעל המוזיקה, ובסוף loudnorm ל־‎-14 LUFS.
