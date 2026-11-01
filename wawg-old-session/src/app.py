import os
import json
import asyncio
import streamlit as st
from openai import OpenAI
import edge_tts

# התאמה ל-MoviePy 2.x החדש (ללא moviepy.editor)
from moviepy import (
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

# פונקציה להיפוך עברית נכון (RTL)
def fix_hebrew(text):
    # אם Pillow נבנתה עם libraqm, היא כבר מסדרת עברית מימין לשמאל בעצמה; היפוך נוסף יהפוך את הטקסט בחזרה
    from PIL import features
    if features.check("raqm"):
        return text
    try:
        from bidi.algorithm import get_display
        return get_display(text)
    except ImportError:
        # פתרון גיבוי ידני אם python-bidi לא מותקנת
        words = text.split(" ")
        reversed_words = [
            w[::-1] if any("֐" <= c <= "ת" for c in w) else w
            for w in words
        ]
        return " ".join(reversed(reversed_words))

# קטלוג הדמויות
CHARACTERS = {
    "maya_tech": {
        "name": "מאיה (מקצועית וטכנולוגית)",
        "voice": "he-IL-HilaNeural",
        "bg_color": (30, 41, 59),
        "accent_color": (56, 189, 248),
        "system_prompt": "אתה מייצר תסריטים קצרים, חדים ומקצועיים ליוצרת תוכן טכנולוגית."
    },
    "dan_creative": {
        "name": "דן (אנרגטי ויצירתי)",
        "voice": "he-IL-AvriNeural",
        "bg_color": (24, 24, 27),
        "accent_color": (250, 204, 21),
        "system_prompt": "אתה מייצר תסריטי סושיאל מהירים, סוחפים וקצביים עם הוק חזק."
    }
}

# בחירת גופן עברי שמתאים גם ללינוקס וגם ל-Windows/Mac
def get_hebrew_font(size):
    font_candidates = [
        "arial.ttf",                                                 # Windows
        "/System/Library/Fonts/Supplemental/Arial.ttf",              # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",     # Linux: עברית + ספרות וסימנים
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",          # Linux (Debian/Ubuntu)
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",           # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path) or font_path == "arial.ttf":
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()

# שבירת טקסט לשורות שנכנסות ברוחב המסגרת (לפני היפוך העברית, כדי שסדר השורות יישאר נכון)
def wrap_lines(draw, text, font, max_width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(fix_hebrew(candidate), font=font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

# יצירת תמונת סצנה והטמעת טקסט מתוקן
def create_scene_image(filename, char_name, text, bg_color, accent_color):
    img = Image.new("RGB", (1080, 1920), color=bg_color)
    draw = ImageDraw.Draw(img)

    # מסגרת מעוצבת
    draw.rectangle([50, 50, 1030, 1870], outline=accent_color, width=8)

    # גופנים
    font_title = get_hebrew_font(60)
    font_text = get_hebrew_font(90)

    # כותרת הדמות
    draw.text((540, 250), fix_hebrew(char_name), fill=accent_color, font=font_title, anchor="mm")

    # טקסט מרכזי, שבור לשורות וממורכז אנכית
    lines = wrap_lines(draw, text, font_text, max_width=860)
    line_height = 120
    top = 960 - (len(lines) - 1) * line_height / 2
    for i, line in enumerate(lines):
        draw.text((540, top + i * line_height), fix_hebrew(line), fill="white", font=font_text, anchor="mm")

    img.save(filename)

# יצירת קובץ קריינות
async def generate_voice(text, voice_id, output_path):
    # בסביבה עם פרוקסי (למשל שרת בענן) edge-tts צריך לקבל אותו במפורש
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    communicate = edge_tts.Communicate(text, voice_id, proxy=proxy)
    await communicate.save(output_path)

# הפקת תסריט (OpenAI או תסריט דמה ידני ללא מפתח)
def generate_script(api_key, character_key, topic, num_scenes):
    if not api_key:
        # תסריט ברירת מחדל אם אין מפתח API
        return {
            "scenes": [
                {"voiceover": f"שלום, היום נדבר על {topic}", "on_screen_text": topic},
                {"voiceover": "הטיפ הראשון הוא לשמור על פשטות", "on_screen_text": "טיפ 1: פשטות"},
                {"voiceover": "עקבו לעוד טיפים ועדכונים", "on_screen_text": "עקבו עכשיו"}
            ][:num_scenes]
        }

    client = OpenAI(api_key=api_key)
    char_info = CHARACTERS[character_key]

    prompt = f"""
    כתוב תסריט קצר בפורמט שורטס (9:16) בנושא: "{topic}".
    מספר סצנות מבוקש: {num_scenes}.
    עבור כל סצנה ספק:
    1. voiceover: הטקסט המדויק להקראה בקול (עד 10 מילים).
    2. on_screen_text: כותרת קצרה שתוצג על המסך (2-4 מילים).

    החזר אך ורק מבנה JSON תקין לפי הפורמט הבא:
    {{
      "scenes": [
        {{"voiceover": "...", "on_screen_text": "..."}}
      ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": char_info["system_prompt"]},
            {"role": "user", "content": prompt}
        ]
    )
    return json.loads(response.choices[0].message.content)

# הרכבת קובץ הווידאו מכל חלקי הסצנות (תואם MoviePy 2.x)
def build_video(scenes, character_key, output_filename="final_video.mp4"):
    os.makedirs("temp", exist_ok=True)
    char_data = CHARACTERS[character_key]
    video_clips = []

    for idx, scene in enumerate(scenes):
        audio_path = f"temp/audio_{idx}.mp3"
        image_path = f"temp/bg_{idx}.png"

        # 1. יצירת סאונד
        asyncio.run(generate_voice(scene["voiceover"], char_data["voice"], audio_path))
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration + 0.3

        # 2. יצירת פריים ויזואלי עם טקסט
        create_scene_image(
            image_path,
            char_data["name"],
            scene["on_screen_text"],
            char_data["bg_color"],
            char_data["accent_color"]
        )

        # 3. סנכרון תמונה וקול (תחביר MoviePy 2.x באמצעות with_duration / with_audio)
        img_clip = ImageClip(image_path)

        # תמיכה לאחור בגרסאות MoviePy ישנות וחדשות במקביל
        if hasattr(img_clip, "with_duration"):
            img_clip = img_clip.with_duration(duration).with_audio(audio_clip)
        else:
            img_clip = img_clip.set_duration(duration).set_audio(audio_clip)

        video_clips.append(img_clip)

    # 4. חיבור כל הקליפים לרצף יחיד ורינדור
    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip.write_videofile(
        output_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    return output_filename

# --- ממשק Streamlit ---
st.set_page_config(page_title="מחולל סרטונים מבוסס AI", layout="centered")
# ממשק מימין לשמאל לעברית; את תצוגת ה-JSON משאירים משמאל לימין
st.markdown(
    "<style>.stApp{direction:rtl;text-align:right}"
    "[data-testid='stJson']{direction:ltr;text-align:left}</style>",
    unsafe_allow_html=True,
)
st.title("מערכת הפקת סרטונים עם שליטה בדמויות")

api_key = st.text_input("OpenAI API Key (אופציונלי - השאר ריק לתסריט לדוגמה)", type="password")

selected_char = st.selectbox(
    "בחר דמות:",
    options=list(CHARACTERS.keys()),
    format_func=lambda x: CHARACTERS[x]["name"]
)

topic = st.text_input("נושא הסרטון:", value="3 טיפים לעיצוב")
scenes_count = st.slider("מספר סצנות:", min_value=2, max_value=5, value=3)

if st.button("ייצר סרטון"):
    with st.spinner("מייצר תסריט..."):
        script_data = generate_script(api_key, selected_char, topic, scenes_count)
        st.json(script_data)

    with st.spinner("מפיק קריינות ומרנדר וידאו..."):
        output_file = build_video(script_data["scenes"], selected_char)
        st.success("הסרטון מוכן!")
        st.video(output_file)
