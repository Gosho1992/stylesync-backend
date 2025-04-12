# ✅ Improved frontend.py with better formatting for AI suggestions
import openai
import streamlit as st
import requests
from PIL import Image
from gtts import gTTS
from deep_translator import GoogleTranslator
import io
import time
from textwrap import wrap
import re

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

# ---------- Helper to Format Text (Improved) ----------
def format_text_block(text):
    # Split into sections if numbered lists are present
    sections = re.split(r'\n\d+\.', text)
    if len(sections) > 1:
        formatted = ""
        for i, section in enumerate(sections[1:], 1):
            section = section.strip()
            if not section:
                continue
            # Add emoji based on content
            emoji = get_section_emoji(section)
            formatted += f"\n{emoji} **{i}. {section.split('.')[0].strip()}**\n"
            # Process the rest of the section
            points = [p.strip() for p in section.split('.')[1:] if p.strip()]
            for point in points[:3]:  # Limit to 3 points per section
                formatted += f"   ◦ {point}\n"
            formatted += "\n"
        return formatted
    
    # For non-numbered content
    paragraphs = text.split("\n")
    formatted = ""
    current_section = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
            
        # Detect section headers
        if p.endswith(":") or any(word in p.lower() for word in 
                                ["outfit", "attire", "accessories", "daywear", 
                                 "nightwear", "tips", "shoes", "summary", 
                                 "jewelry", "temple", "trends", "men", "women"]):
            if current_section:
                formatted += f"\n{format_paragraphs(current_section)}\n"
                current_section = ""
            emoji = get_section_emoji(p)
            formatted += f"\n{emoji} **{p}**\n\n"
        else:
            current_section += p + "\n"
    
    if current_section:
        formatted += f"\n{format_paragraphs(current_section)}\n"
    
    return formatted

def format_paragraphs(text, max_lines=3):
    """Break long paragraphs into shorter chunks"""
    sentences = re.split(r'(?<=[.!?]) +', text)
    formatted = ""
    current_line = ""
    
    for sentence in sentences:
        if len(current_line.split('\n')) >= max_lines:
            formatted += current_line + "\n\n"
            current_line = ""
        current_line += sentence + " "
    
    if current_line:
        formatted += current_line
    
    return formatted.strip()

def get_section_emoji(text):
    """Get appropriate emoji based on section content"""
    text = text.lower()
    if any(word in text for word in ['shirt', 'top', 'blouse']):
        return "👕"
    elif any(word in text for word in ['pant', 'trouser', 'jeans']):
        return "👖"
    elif any(word in text for word in ['dress', 'skirt', 'gown']):
        return "👗"
    elif any(word in text for word in ['shoe', 'boot', 'sandal']):
        return "👠"
    elif any(word in text for word in ['accessor', 'jewelry', 'bag']):
        return "💍"
    elif any(word in text for word in ['men', 'male', 'gentleman']):
        return "👨"
    elif any(word in text for word in ['women', 'female', 'lady']):
        return "👩"
    elif any(word in text for word in ['summer', 'hot', 'warm']):
        return "☀️"
    elif any(word in text for word in ['winter', 'cold', 'chilly']):
        return "❄️"
    elif any(word in text for word in ['casual', 'everyday']):
        return "😊"
    elif any(word in text for word in ['formal', 'office', 'business']):
        return "💼"
    elif any(word in text for word in ['party', 'night', 'club']):
        return "🎉"
    return "✨"

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
    time.sleep(3)
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
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .stMarkdown, .stImage {
            background-color: rgba(255, 255, 255, 0.9);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }

        h1.center {
            text-align: center;
            font-size: 2.2rem;
            color: #333;
        }

        .tts-button {
            margin-top: 10px;
        }
        
        .suggestion-card {
            border-left: 4px solid #bb377d;
            padding-left: 1rem;
            margin: 1rem 0;
        }
        
        .trend-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 3px solid #fbc2eb;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.image("https://i.imgur.com/y0ywLko.jpeg", width=100)
st.sidebar.title("👗 StyleSync AI")
st.sidebar.markdown("""
Your AI-powered fashion assistant 👚  
Upload your clothing item and get personalized fashion advice ✨
""")
st.sidebar.markdown("---")
st.sidebar.caption("Created by gosho1992 • [GitHub](https://github.com/Gosho1992)")

with st.sidebar.expander("ℹ️ How It Works"):
    st.markdown("""
    1. 📸 Upload an image of your clothing item  
    2. 🎯 Select Occasion, Season, Age Group, and Mood  
    3. ✨ AI generates matching outfit suggestions  
    4. 💾 Download or listen to your personalized style tips!
    """)

with st.sidebar.expander("🧠 What is Style Memory?"):
    st.markdown("""
    Style Memory keeps track of outfits you've uploaded:  
    - 📦 Stores your fashion preferences  
    - 🔄 Recommends new combinations  
    - 💡 Learns from your choices over time
    """)

language_option = st.sidebar.selectbox("🌐 Choose Language for Suggestions", 
                                     ["English", "Roman Urdu", "French", "German", "Portuguese"])
lang_codes = {
    "English": "en",
    "Roman Urdu": "ur",
    "French": "fr",
    "German": "de",
    "Portuguese": "pt"
}

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Assistant", "📊 Trends"])

# ---------- Tab 1: Outfit Suggestion ----------
with tab1:
    st.header("👕 AI Fashion Outfit Suggestions")
    col1, col2 = st.columns(2)
    with col1:
        occasion = st.selectbox("🎯 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"], key="occasion1")
        season = st.selectbox("🌦️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"], key="season1")
    with col2:
        age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"], key="age1")
        mood = st.selectbox("😌 Mood", ["Happy", "Lazy", "Motivated", "Romantic", "Confident", 
                                      "Chill", "Adventurous", "Classy", "Energetic", "Bold", 
                                      "Elegant", "Sad"], key="mood1")
    
    uploaded_file = st.file_uploader("📷 Upload Clothing Image (JPEG/PNG)", type=["jpg", "jpeg", "png"])
    
    if st.button("✨ Generate Fashion Suggestion", key="suggest1") and uploaded_file:
        image = Image.open(uploaded_file).convert("RGB").resize((500, 500))
        st.image(image, caption="📸 Your Uploaded Item", use_container_width=True)
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}
        data = {"occasion": occasion, "season": season, "age": age, "mood": mood}

        with st.spinner("🧠 Analyzing your style and generating perfect suggestions..."):
            response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files, data=data)
            if response.status_code == 200:
                suggestion = response.json()["fashion_suggestion"]
                translated = translate_long_text(suggestion, lang_codes[language_option])
                formatted = format_text_block(translated)
                
                st.success("🎉 Your Personalized Fashion Recommendation")
                st.markdown(f"""
                <div class="suggestion-card">
                {formatted}
                </div>
                """, unsafe_allow_html=True)
                
                # Add TTS button
                tts_button = st.button("🔊 Listen to Suggestion")
                if tts_button:
                    tts = gTTS(translated, lang=lang_codes[language_option])
                    tts.save("suggestion.mp3")
                    st.audio("suggestion.mp3")
            else:
                st.error(f"⚠️ Error {response.status_code}: {response.text}")

# ---------- Tab 2: Travel Assistant ----------
with tab2:
    st.header("✈️ Travel Fashion Assistant")
    st.markdown("Get culturally appropriate outfit suggestions for your destination")
    
    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input("🌍 Destination (City/Country)")
            travel_season = st.selectbox("📅 Season", ["Spring", "Summer", "Autumn", "Winter"], key="season2")
        with col2:
            trip_type = st.selectbox("🧳 Trip Type", ["Casual", "Business", "Wedding", "Adventure"], key="trip2")
            travel_age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"], key="age2")
        
        submitted = st.form_submit_button("🌟 Get Travel Style Guide")

    if submitted and destination:
        travel_prompt = (
            f"Provide concise, bullet-point fashion advice for traveling to {destination} during {travel_season}.\n"
            f"Focus on: 1) Cultural appropriateness 2) Weather suitability 3) {trip_type} attire 4) Key items to pack.\n"
            f"Separate suggestions for men and women. Keep each point under 10 words. Include emojis."
        )

        with st.spinner("✈️ Researching fashion norms for {destination}..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a concise travel fashion advisor. Use bullet points, emojis, and keep suggestions very brief."},
                    {"role": "user", "content": travel_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])
            formatted = format_text_block(translated)
            
            st.success(f"🧳 {destination} Travel Style Guide")
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px;">
            {formatted}
            </div>
            """, unsafe_allow_html=True)

# ---------- Tab 3: Fashion Trends ----------
with tab3:
    st.header("📊 Current Fashion Trends")
    st.markdown("Discover what's trending around the world")
    
    region = st.selectbox("🌍 Select Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"], key="region3")
    
    if st.button("👀 Show Current Trends", key="trends_btn"):
        trend_prompt = (
            f"List the top 5 fashion trends in {region} for men and women.\n"
            f"Format as: 'Gender: Trend name - Brief description (3-5 words)'\n"
            f"Add relevant emojis and separate by gender.\n"
            f"Keep each trend to one line maximum."
        )

        with st.spinner(f"🔍 Analyzing {region} fashion trends..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion trends expert. Provide concise, emoji-rich trend reports."},
                    {"role": "user", "content": trend_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])
            
            # Enhanced formatting for trends
            st.success(f"🔥 Current Trends in {region}")
            
            if "Women:" in translated and "Men:" in translated:
    try:
        women_trends, men_trends = translated.split("Men:")
        st.subheader("👩 Women's Trends")
        for line in women_trends.replace("Women:", "").strip().split('\n'):
            if line.strip():
                st.markdown(f"<div class='trend-item'>✨ {line.strip()}</div>", unsafe_allow_html=True)

        st.subheader("👨 Men's Trends")
        for line in men_trends.strip().split('\n'):
            if line.strip():
                st.markdown(f"<div class='trend-item'>✨ {line.strip()}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.warning("⚠️ Could not split content into men/women sections.")
        st.markdown(f"<div class='trend-item'>{translated}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='trend-item'>{translated}</div>", unsafe_allow_html=True)