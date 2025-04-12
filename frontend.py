# ✅ Final frontend.py with proper formatting for all 3 tabs
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

# ---------- Helper to Format Text ----------
def format_text_block(text):
    paragraphs = text.split("\n")
    formatted = ""
    for p in paragraphs:
        if len(p.strip()) == 0:
            continue
        p = p.replace("**", "")
        if any(word in p.lower() for word in ["outfit", "attire", "accessories", "daywear", "nightwear", "tips", "shoes", "summary", "jewelry", "temple", "trends"]):
            formatted += f"\n**👉 {p.strip()}**\n\n"
        else:
            formatted += f"{p.strip()}\n\n"
    return formatted

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
st.sidebar.markdown("Upload your clothing item and get personalized fashion advice ✨")

if st.sidebar.button("🔁 Start Over"):
    st.session_state.clear()
    st.rerun()

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
                formatted = format_text_block(translated)
                st.success("🎨 Your AI Fashion Suggestion")
                st.markdown(formatted)
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
            f"You're a travel stylist familiar with fashion and cultural norms.\n"
            f"I'm traveling to {destination} during {travel_season} for a {trip_type} trip. I'm in my {travel_age}.\n"
            f"Suggest culturally appropriate and fashionable outfits for this region and weather."
        )

        with st.spinner("Compiling your wardrobe..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cultural fashion advisor."},
                    {"role": "user", "content": travel_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])
            formatted = format_text_block(translated)
            st.success("🌴 Travel Style Tips")
            st.markdown(formatted)

# ---------- Tab 3: Fashion Trends ----------
with tab3:
    st.header("🧵 Fashion Trends")
    region = st.selectbox("🌍 Select Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"], key="region3")

    if st.button("📊 Show Trends"):
        trend_prompt = (
            f"You're a fashion trend analyst with cultural insight.\n"
            f"What are the top style trends in {region} for men and women?\n"
            f"Keep it modern, separated by gender, and well structured."
        )

        with st.spinner("Fetching trends for you..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion trends expert with global knowledge."},
                    {"role": "user", "content": trend_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])
            formatted = format_text_block(translated)
            st.success("🧥 Current Fashion Trends")
            st.markdown(formatted)
