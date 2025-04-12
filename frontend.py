import openai
import streamlit as st
import requests
from PIL import Image
from gtts import gTTS
from deep_translator import GoogleTranslator
import io
import time
from textwrap import wrap

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="StyleSync", layout="wide")

# ---------- Helper for Long Translations ----------
def translate_long_text(text, target_lang):
    chunks = wrap(text, width=4500)
    translated_chunks = [
        GoogleTranslator(source='auto', target=target_lang).translate(chunk)
        for chunk in chunks
    ]
    return "\n\n".join(translated_chunks)

# ---------- Welcome Splash (Once per session) ----------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome:
    st.markdown("""
        <div style='background: linear-gradient(to right, #fbd3e9, #bb377d); height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; color: white; text-align:center;'>
            <h1 style='font-size: 4rem;'>Welcome to StyleSync</h1>
            <p style='font-size: 1.5rem;'>Your AI-powered clothing assistant</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(5)
    st.session_state.show_welcome = False
    st.rerun()

# ---------- CSS ----------
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(45deg, #ff9a9e, #fad0c4, #fbc2eb, #a18cd1, #a1c4fd, #d4fc79, #96e6a1);
            background-size: 200% 200%;
            animation: rainbow 10s ease infinite;
            padding: 2rem;
        }
        @keyframes rainbow {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .stMarkdown, .stImage {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.image("https://i.imgur.com/y0ywLko.jpeg", width=100)
st.sidebar.title("👗 StyleSync AI")
st.sidebar.markdown("""
Your AI-powered fashion assistant 👚  
Upload your clothing item and get matching outfit suggestions powered by GPT-4.
""")
st.sidebar.markdown("---")
if st.sidebar.button("🔁 Start Over"):
    st.session_state.clear()
    st.rerun()

language_option = st.sidebar.selectbox("🌐 Choose Language", ["English", "Roman Urdu", "French", "German", "Portuguese"])
lang_codes = {
    "English": "en",
    "Roman Urdu": "ur",
    "French": "fr",
    "German": "de",
    "Portuguese": "pt"
}

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Fashion Assistant", "🧵 Fashion Trends"])

# ---------- Tab 1 ----------
with tab1:
    st.header("👕 AI Fashion Outfit Suggestions")
    occasion = st.selectbox("🎯 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
    season = st.selectbox("🌦️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])
    age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
    mood = st.selectbox("😌 Mood", ["Happy", "Lazy", "Motivated", "Romantic", "Confident", "Chill", "Adventurous", "Classy", "Energetic", "Bold", "Elegant", "Sad"])
    uploaded_file = st.file_uploader("📷 Upload Clothing Image", type=["jpg", "jpeg", "png"])

    if st.button("✨ Generate Outfit Suggestion") and uploaded_file:
        image = Image.open(uploaded_file).convert("RGB").resize((500, 500))
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG", quality=70)
        img_bytes.seek(0)

        files = {'file': ('resized.jpg', img_bytes, 'image/jpeg')}
        data = {"occasion": occasion, "season": season, "age": age, "mood": mood}

        with st.spinner("Analyzing your style..."):
            try:
                res = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files, data=data)
                if res.status_code == 200:
                    result = res.json()["fashion_suggestion"]
                    cleaned = result.replace("**", "")
                    formatted = "\n\n".join(cleaned.split(". "))
                    translated = translate_long_text(formatted, lang_codes[language_option])
                    st.success("✅ Outfit Suggestion")
                    st.markdown(translated)
                    if st.button("🔊 Listen"):
                        tts = gTTS(translated, lang=lang_codes[language_option])
                        tts_bytes = io.BytesIO()
                        tts.write_to_fp(tts_bytes)
                        tts_bytes.seek(0)
                        st.audio(tts_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"Error: {e}")

# ---------- Tab 2 ----------
with tab2:
    st.header("✈️ Travel Fashion Assistant")
    destination = st.text_input("🌍 Destination")
    travel_season = st.selectbox("📅 Season", ["Spring", "Summer", "Autumn", "Winter"])
    trip_type = st.selectbox("🧳 Trip Type", ["Casual", "Business", "Wedding", "Adventure"])
    travel_age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])

    if st.button("🌟 Generate Travel Suggestion"):
        travel_prompt = (
            f"You're a travel fashion expert. I'm going to {destination} in {travel_season} for a {trip_type} trip. "
            f"I'm in my {travel_age}. Suggest outfits considering culture and weather."
        )
        with st.spinner("Packing your style..."):
            try:
                res = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a travel stylist who respects cultural values."},
                        {"role": "user", "content": travel_prompt}
                    ],
                    max_tokens=500
                )
                travel_result = res.choices[0].message.content.replace("**", "")
                formatted = "\n\n".join(travel_result.split(". "))
                translated = translate_long_text(formatted, lang_codes[language_option])
                st.success("✅ Travel Suggestion")
                st.markdown(translated)
                if st.button("🔊 Listen to Travel Tip"):
                    tts = gTTS(translated, lang=lang_codes[language_option])
                    tts_bytes = io.BytesIO()
                    tts.write_to_fp(tts_bytes)
                    tts_bytes.seek(0)
                    st.audio(tts_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"Error: {e}")

# ---------- Tab 3 ----------
with tab3:
    st.header("🧵 Fashion Trends")
    region = st.selectbox("🌎 Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"])

    if st.button("🔍 Show Trends"):
        trend_prompt = f"You're a global fashion trend expert. Summarize current trends in {region} for both men and women."
        with st.spinner("Fetching the latest trends..."):
            try:
                res = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a global fashion trend expert."},
                        {"role": "user", "content": trend_prompt}
                    ],
                    max_tokens=500
                )
                trend_result = res.choices[0].message.content.replace("**", "")
                formatted = "\n\n".join(trend_result.split(". "))
                translated = translate_long_text(formatted, lang_codes[language_option])
                st.success("🌟 Fashion Trends")
                st.markdown(translated)
                if st.button("🔊 Listen to Trends"):
                    tts = gTTS(translated, lang=lang_codes[language_option])
                    tts_bytes = io.BytesIO()
                    tts.write_to_fp(tts_bytes)
                    tts_bytes.seek(0)
                    st.audio(tts_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"Error: {e}")
