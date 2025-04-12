# ✅ Updated frontend.py with unique keys and better formatting for all tabs
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

# ---------- CSS Styling ----------
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to right, #ffecd2, #fcb69f);
            background-size: cover;
            padding: 2rem;
        }
        .stMarkdown, .stImage {
            background-color: #fff8f0;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3 {
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.image("https://i.imgur.com/y0ywLko.jpeg", width=100)
st.sidebar.title("👗 StyleSync AI")
st.sidebar.markdown("Upload your clothing item and get personalized fashion advice ✨")

if st.sidebar.button("🔁 Start Over"):
    st.session_state.clear()
    st.experimental_rerun()

language_option = st.sidebar.selectbox("🌐 Choose Language", ["English", "Roman Urdu", "French", "German", "Portuguese"])
lang_codes = {"English": "en", "Roman Urdu": "ur", "French": "fr", "German": "de", "Portuguese": "pt"}

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Assistant", "🧵 Trends"])

# ---------- Tab 1: Outfit Suggestion ----------
with tab1:
    st.header("👕 AI Fashion Outfit Suggestions")
    occasion = st.selectbox("🎯 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"], key="occasion1")
    season = st.selectbox("🌦️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"], key="season1")
    age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"], key="age1")
    mood = st.selectbox("😌 Mood", ["Happy", "Lazy", "Motivated", "Romantic", "Confident", "Chill", "Adventurous", "Classy", "Energetic", "Bold", "Elegant", "Sad"], key="mood1")
    uploaded_file = st.file_uploader("📷 Upload Image", type=["jpg", "jpeg", "png"])

    if st.button("✨ Generate Suggestion") and uploaded_file:
        image = Image.open(uploaded_file).convert("RGB").resize((500, 500))
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}
        data = {"occasion": occasion, "season": season, "age": age, "mood": mood}

        with st.spinner("Analyzing style..."):
            response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files, data=data)
            if response.status_code == 200:
                suggestion = response.json()["fashion_suggestion"]
                translated = translate_long_text(suggestion, lang_codes[language_option])
                st.success("🎨 Your AI Fashion Suggestion")
                st.markdown(translated.replace("**", ""))
            else:
                st.error(f"Backend Error {response.status_code}: {response.text}")

# ---------- Tab 2: Travel Assistant ----------
with tab2:
    st.header("✈️ Travel Fashion Assistant")
    with st.form("travel_form"):
        destination = st.text_input("🌍 Destination")
        travel_season = st.selectbox("📅 Season", ["Spring", "Summer", "Autumn", "Winter"], key="season2")
        trip_type = st.selectbox("🧳 Trip Type", ["Casual", "Business", "Wedding", "Adventure"], key="trip2")
        travel_age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"], key="age2")
        submitted = st.form_submit_button("🌟 Generate Travel Suggestion")

    if submitted:
        travel_prompt = (
            f"You're a travel stylist familiar with fashion and cultural norms.
            I'm going to {destination} this {travel_season} for a {trip_type} trip. I'm in my {travel_age}.
            Suggest culturally appropriate and stylish outfits." )

        with st.spinner("Compiling your wardrobe..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cultural fashion advisor."},
                    {"role": "user", "content": travel_prompt}
                ],
                max_tokens=500
            )
            travel_result = response.choices[0].message.content.strip()
            translated = translate_long_text(travel_result, lang_codes[language_option])
            st.success("🌴 Travel Style Tips")
            st.markdown(translated.replace("**", ""))

# ---------- Tab 3: Fashion Trends ----------
with tab3:
    st.header("🧵 Fashion Trends")
    region = st.selectbox("🌍 Select Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"], key="region3")

    if st.button("📊 Show Trends"):
        trend_prompt = (
            f"You're a fashion trend analyst with cultural insight.
            What are the top style trends in {region} for men and women?
            Keep it modern, separated by gender, and well structured."
        )

        with st.spinner("Fetching trends for you..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion trends expert with global knowledge."},
                    {"role": "user", "content": trend_prompt}
                ],
                max_tokens=500
            )
            trend_result = response.choices[0].message.content.strip()
            translated = translate_long_text(trend_result, lang_codes[language_option])
            st.success("🧥 Current Fashion Trends")
            st.markdown(translated.replace("**", ""))
