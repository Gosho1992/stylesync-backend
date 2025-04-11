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
        <div style='background: linear-gradient(to right, #fbd3e9, #bb377d);
                    height:100vh; display:flex; flex-direction:column;
                    justify-content:center; align-items:center;
                    color: white; text-align:center;'>
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
            background: linear-gradient(45deg, 
                #ff9a9e, #fad0c4, #fbc2eb, #a18cd1, 
                #fbc2eb, #ff9a9e, #fbc2eb, #a1c4fd, 
                #c2e9fb, #d4fc79, #96e6a1);
            background-size: 200% 200%;
            animation: rainbow 10s ease infinite;
            padding: 2rem;
        }

        @keyframes rainbow {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }

        .stButton>button {
            background-color: #0066cc;
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 8px;
        }

        .stMarkdown, .stImage {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.05);
        }

        h1.center {
            text-align: center;
            font-size: 2.2rem;
        }

        .tts-button {
            margin-top: 10px;
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
st.sidebar.caption("Created by gosho1992 • [GitHub](https://github.com/Gosho1992)")

if st.sidebar.button("🔁 Start Over"):
    st.session_state.clear()
    st.experimental_rerun()

with st.sidebar.expander("ℹ️ How It Works"):
    st.markdown("""
    1. 📤 Upload an image of your clothing item (shirt, dress, etc.)
    2. 🎯 Select Occasion, Season, Age Group, and Mood
    3. 🚀 Press 'Generate Suggestion'
    4. 🧠 AI will generate a personalized outfit
    """)

language_option = st.sidebar.selectbox("🌐 Choose Language for Suggestions", ["English", "Roman Urdu", "French", "German", "Portuguese"])
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
    st.markdown("<h1 class='center'>👕 AI Fashion Outfit Suggestions</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload an image, select filters and get your style!</p>", unsafe_allow_html=True)

    occasion = st.selectbox("🎯 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
    season = st.selectbox("🌦️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])
    age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
    mood = st.selectbox("😌 Mood", ["Happy", "Lazy", "Motivated", "Romantic", "Confident", "Chill", "Adventurous", "Classy", "Energetic", "Bold", "Elegant", "Sad"])
    style_memory_enabled = st.toggle("💾 Enable Style Memory", value=False)
    uploaded_file = st.file_uploader("📷 Upload image...", type=["jpg", "jpeg", "png"])

    with st.form("outfit_form"):
        submitted = st.form_submit_button("✨ Generate Suggestion")

    if submitted and uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        image = image.resize((500, 500))
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG", quality=70)
        img_bytes.seek(0)

        data = {"occasion": occasion, "season": season, "age": age, "mood": mood}
        files = {'file': ('resized.jpg', img_bytes, 'image/jpeg')}

        with st.spinner("Analyzing outfit..."):
            try:
                response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    suggestion = result["fashion_suggestion"]
                    translated = translate_long_text(suggestion, lang_codes[language_option])
                    st.success("✅ AI Suggestion:")
                    st.markdown(translated, unsafe_allow_html=True)

                    st.download_button("📥 Download Suggestion", translated, file_name="style_suggestion.txt", mime="text/plain")
                    if st.button("🔊 Listen"):
                        tts = gTTS(text=translated, lang=lang_codes[language_option])
                        tts_bytes = io.BytesIO()
                        tts.write_to_fp(tts_bytes)
                        tts_bytes.seek(0)
                        st.audio(tts_bytes, format="audio/mp3")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

        if style_memory_enabled:
            if "style_memory" not in st.session_state:
                st.session_state.style_memory = []
            st.session_state.style_memory.append(image)
            if st.session_state.style_memory:
                st.markdown("<h3>🧠 Style Memory</h3>", unsafe_allow_html=True)
                for img in st.session_state.style_memory:
                    st.image(img, width=200)

# ---------- Tab 2 ----------
with tab2:
    st.markdown("<h2>✈️ Travel Fashion Assistant</h2>", unsafe_allow_html=True)
    with st.form("travel_form"):
        destination = st.text_input("🌍 Destination")
        travel_season = st.selectbox("📅 Season", ["Spring", "Summer", "Autumn", "Winter"])
        trip_type = st.selectbox("🧳 Trip Type", ["Casual", "Business", "Wedding", "Adventure"])
        age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
        go = st.form_submit_button("🌟 Generate Travel Suggestion")

        if go and destination:
            travel_prompt = (
                f"You're a travel fashion expert who knows global and cultural style.\n"
                f"I'm traveling to {destination} during {travel_season}, for a {trip_type.lower()} trip. I'm in my {age}.\n"
                f"Suggest fashionable outfits, keeping cultural preferences and weather in mind."
            )
            with st.spinner("Generating travel style..."):
                try:
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a travel fashion stylist who knows worldwide fashion and cultural norms."},
                            {"role": "user", "content": travel_prompt}
                        ],
                        max_tokens=400
                    )
                    suggestion = response.choices[0].message.content.strip()
                    translated = translate_long_text(suggestion, lang_codes[language_option])
                    st.success("✅ Travel Suggestion:")
                    st.markdown(translated)
                    if st.button("🔊 Listen"):
                        tts = gTTS(text=translated, lang=lang_codes[language_option])
                        tts_bytes = io.BytesIO()
                        tts.write_to_fp(tts_bytes)
                        tts_bytes.seek(0)
                        st.audio(tts_bytes, format="audio/mp3")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")

# ---------- Tab 3 ----------
with tab3:
    st.markdown("<h2>🧵 Fashion Trends</h2>", unsafe_allow_html=True)
    region = st.selectbox("🌍 Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"])
    if st.button("✨ Show Trends"):
        with st.spinner("Fetching regional trends..."):
            try:
                prompt = (
                    f"You're a fashion trend expert who knows recent style waves and cultural fashion norms.\n"
                    f"What are the current trending styles in {region}? Summarize it clearly for both men and women."
                )
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a global fashion trend expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300
                )
                trend_result = response.choices[0].message.content.strip()
                translated = translate_long_text(trend_result, lang_codes[language_option])
                st.success("🌟 Fashion Trends:")
                st.markdown(translated)
                if st.button("🔊 Listen"):
                    tts = gTTS(text=translated, lang=lang_codes[language_option])
                    tts_bytes = io.BytesIO()
                    tts.write_to_fp(tts_bytes)
                    tts_bytes.seek(0)
                    st.audio(tts_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"❌ Exception: {e}")
