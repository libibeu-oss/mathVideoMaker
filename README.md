# mathVideoMaker — סרטוני הסבר במתמטיקה + דפים אינטראקטיביים, עם Claude

Skill ל־Claude שהופך נושא מתמטי לשני תוצרים תואמים:
- **סרטון הסבר (MP4)** — מראה *למה* משהו נכון, צעד אחר צעד, עם כתוביות.
- **דף אינטראקטיבי (קובץ HTML אחד)** — סליידרים שמשנים את אותם פרמטרים, כדי לשחק עם המושג.

שני התוצרים חולקים אותם סימונים, טווחים וצבעים. הסרטון מסביר, הדף נותן להתנסות.

> מבוסס על [GordenSun/mathVideoMaker](https://github.com/GordenSun/mathVideoMaker) (Skill ל־Cursor, בסינית).
> הגרסה הזו הותאמה ל־Claude: הוראות באנגלית, תמיכה מלאה בעברית (מימין לשמאל), ומנוע אנימציה קל
> שעובד גם בלי Manim — למשל בסביבת הענן של Claude, שבה אי אפשר להתקין חבילות.

## דוגמאות מוכנות (בעברית)

| נושא | סרטון | דף אינטראקטיבי |
|------|-------|----------------|
| משפט פיתגורס — הוכחה בסידור מחדש | [`videos/pythagoras/Pythagoras.mp4`](videos/pythagoras/Pythagoras.mp4) | [`videos/pythagoras/index.html`](videos/pythagoras/index.html) |
| כמה שווה הקופסה? `5 × □ = 4 × □ + 7` (יסודי) | [`videos/box-equation/BoxEquation.mp4`](videos/box-equation/BoxEquation.mp4) | [`videos/box-equation/index.html`](videos/box-equation/index.html) |
| הפרבולה `y = n·x²` — מה עושה n? | [`videos/parabola-n/ParabolaN.mp4`](videos/parabola-n/ParabolaN.mp4) | [`videos/parabola-n/index.html`](videos/parabola-n/index.html) |

בכל תיקייה יש גם `storyboard.md` (התכנון) ו־`scene.py` (קוד הסרטון).
הדוגמה המקורית בסינית: [`examples/BoxDivide.mp4`](examples/BoxDivide.mp4).

## התקנה

**Claude.ai / אפליקציית Claude** — דחסו את התיקייה `skills/math-explainer/` לקובץ zip והעלו אותו
בהגדרות, בחלק של ה־Skills.

**Claude Code** — העתיקו את התיקייה לתיקיית ה־Skills:
```bash
git clone https://github.com/libibeu-oss/mathVideoMaker.git
cp -R mathVideoMaker/skills/math-explainer ~/.claude/skills/          # לכל הפרויקטים
# או: cp -R mathVideoMaker/skills/math-explainer <project>/.claude/skills/
```

## שימוש

פשוט מבקשים מ־Claude, למשל:
- "תכין סרטון שמסביר את משפט פיתגורס"
- "תסביר לילדים בכיתה ג׳ איך פותרים 5 × □ = 4 × □ + 7"
- "תראה מה קורה לגרף של y = n·x² כש־n משתנה"

Claude עובד לפי השלבים ב־`SKILL.md`: סטוריבורד ← בדיקת סביבה ← סרטון ← דף ← בדיקות ← מסירה.

## שני מנועים לסרטון

`scripts/check_env.py` בודק מה זמין ובוחר:

| מנוע | מתי | צריך |
|------|-----|------|
| **Manim** | כשהוא מותקן (למשל במחשב שלכם) | `scripts/setup_manim.sh` מתקין הכל |
| **mathviz_lite** | כשאין Manim (ברירת המחדל בענן) | numpy, Pillow, opencv, ffmpeg |

`mathviz_lite` (בקובץ `templates/mathviz_lite.py`) כולל:
- טקסט בעברית מימין לשמאל, עם ביטויים מתמטיים שנשארים בסדר הנכון (`3² + 4² = 5²`).
- צורות חלקות, אנימציות (הופעה, ציור, כתיבה, תנועה, שינוי צורה), צירים וגרפים.
- בדיקות אוטומטיות: גליפים חסרים בגופן, יציאה מהמסך וחפיפת טקסט.
- תצוגה מקדימה מהירה של תמונות מפתח (`MATHVIZ_PREVIEW=1 MATHVIZ_SNAP_DIR=...`).
- גופן Rubik מצורף (רישיון OFL).

רינדור דוגמה:
```bash
python3 videos/pythagoras/scene.py                     # 1080p
MATHVIZ_QUALITY=m python3 videos/pythagoras/scene.py   # 720p, מהיר יותר
```

## מבנה

```
mathVideoMaker/
├── skills/math-explainer/      # ה־Skill עצמו (את זה מתקינים)
│   ├── SKILL.md                # השלבים וכללי האיכות
│   ├── references/             # פדגוגיה וסטוריבורד, Manim, דפים אינטראקטיביים (בסינית)
│   ├── scripts/                # check_env / check_text / check_web / render / setup
│   └── templates/              # mathviz_lite, תבניות סצנה, דף, סטוריבורד, גופנים
├── videos/                     # שלוש הדוגמאות בעברית
└── examples/                   # הדוגמה המקורית
```

---

תודה ל־GordenSun על ה־Skill המקורי ולקהילת [LinuxDO](https://linux.do).
