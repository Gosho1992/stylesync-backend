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

# ---------- Tab 1: Outfit Suggestion (Enhanced Version) ---------- 
with tab1:
    st.header("👑 Personal Style Architect")
    
    # Style Preferences
    with st.expander("✨ Style Blueprint", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            occasion = st.selectbox("🎯 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work", "Date"], key="occasion1")
            season = st.selectbox("🌦️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn", "Monsoon"], key="season1")
        with col2:
            gender = st.selectbox("🚻 Gender", ["Woman", "Man", "Non-binary", "Prefer not to say"], key="gender1")
            body_type = st.selectbox("🧍 Body Type", ["Petite", "Tall", "Plus-size", "Athletic", "Average", "Curvy"], key="bodytype1")
        with col3:
            age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+", "60+"], key="age1")
            mood = st.selectbox("😌 Mood", ["Happy", "Lazy", "Motivated", "Romantic", "Confident", "Chill", "Adventurous", "Classy", "Energetic", "Bold", "Elegant", "Sophisticated", "Edgy"], key="mood1")

    # Image Upload
    uploaded_file = st.file_uploader("📸 Upload Your Style Canvas", type=["jpg", "jpeg", "png"],
                                   help="Use well-lit, front-facing images for best results")

    # Generate button (visible always)
    generate = st.button("✨ Generate Masterpiece", type="primary", use_container_width=True)

    if uploaded_file:
        st.image(Image.open(uploaded_file), caption="🎨 Your Style Foundation", width=300)

    if uploaded_file and generate:
        # Prepare enhanced request data
        data = {
            "occasion": occasion,
            "season": season,
            "gender": gender,
            "body_type": body_type,
            "age": age,
            "mood": mood,
            "format_instructions": """Respond in this STRUCTURE:

## LOOK 1: [Theme Name]
- ✨ **Vibe**: [2-word mood descriptor]
- 👗 **Top**: [Item] + [Fabric/Cut Detail] + [Styling Tip]
- 👖 **Bottom**: [Item] + [Fit Note] + [Trend Reference]
- 👟 **Shoes**: [Type] + [Height/Comfort] + [Seasonal Advice]
- 🧥 **Layers**: [Item] + [Weather Adaptability] + [Cultural Nod]
- 💎 **Accents**: [3 items with functional/personal benefits]
- 📏 **Fit Hack**: [Body-type specific trick]

## LOOK 2: [Different Theme]
[Same structure]

💡 **Style Alchemy**: [1 transformative tip combining 2+ filters]"""
        }

        with st.status("🎨 Crafting your couture vision...", expanded=True):
            try:
                response = requests.post(
                    "https://stylesync-backend-2kz6.onrender.com/upload",
                    files={'file': ('image.jpg', uploaded_file.getvalue(), 'image/jpeg')},
                    data=data,
                    timeout=25
                )

                if response.status_code == 200:
                    suggestion = response.json().get("fashion_suggestion", "")
                    
                    if not suggestion:
                        st.error("🎭 Our stylists need more inspiration! Try again.")
                    else:
                        st.balloons()
                        st.success("🌟 Style Masterpiece Completed!")
                        
                        

                        # Styled response box
                        
                         st.markdown(f"""
                            <div style='background: linear-gradient(to right, #fdfbfb, #ebedee);
                                        padding: 2rem; border-radius: 15px;
                                        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
                                        font-size: 1.05rem; line-height: 1.7rem;'>
                            {suggestion.replace("**", "")}
                            </div>
                        """, unsafe_allow_html=True)

                        # Style breakdown
                        with st.expander("📋 Filters Recap", expanded=False):
                            st.markdown(f"""
                                | Filter | Value |
                                |--------|--------|
                                | Gender | {gender} |
                                | Body Type | {body_type} |
                                | Age | {age} |
                                | Mood | {mood} |
                                | Occasion | {occasion} |
                                | Season | {season} |
                            """)
                        
                        # Audio Button
                        if st.button("🎧 Hear Your Style Story"):
                            with st.spinner("Composing your fashion sonnet..."):
                                tts = gTTS(suggestion, lang=lang_codes[language_option])
                                audio_bytes = io.BytesIO()
                                tts.write_to_fp(audio_bytes)
                                audio_bytes.seek(0)
                                st.audio(audio_bytes, format="audio/mp3")

                else:
                    st.error(f"⚠️ Creative Block (Error {response.status_code})")

            except requests.exceptions.RequestException:
                st.error("🌐 Connection Error: Our stylists are offline.")
            except Exception as e:
                st.error(f"❗ Unexpected Error: {str(e)}")


# ---------- Tab 2: Travel Assistant (Trends-style format) ----------
with tab2:
    st.header("✈️ Travel Fashion Assistant")
    st.markdown("Get **emoji-packed, concise** outfit suggestions for your destination")
    
    with st.form("travel_form"):
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input("🌍 Destination (City/Country)")
            travel_season = st.selectbox("📅 Season", ["Spring", "Summer", "Autumn", "Winter"], key="season2")
        with col2:
            trip_type = st.selectbox("🧳 Trip Type", ["Casual", "Business", "Wedding", "Adventure"], key="trip2")
            travel_age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"], key="age2")
        
        submitted = st.form_submit_button("🌟 Generate Trendy Travel Guide")

    if submitted and destination:
        travel_prompt = (
            f"""You are a fashion-forward travel stylist. I'm a {travel_age} traveler going to {destination} for {trip_type} during {travel_season}.
            
            Give me **5 ultra-concise fashion recommendations per gender** with:
            - 🔥 Trendy yet practical items
            - 🌦️ Weather-appropriate fabrics
            - 🏛️ Cultural considerations
            - ✨ 1 emoji per line
            - 🚫 Max 8 words per bullet
            
            Format EXACTLY like this:
            Women:
            👗 Silk midi dress (elegant + breathable)
            🧥 Light trench coat (spring-ready)
            
            Men:
            👔 Linen shirt (wrinkle-resistant)
            🧳 Compact duffel (airline-approved)
            """
        )

        with st.spinner(f"✈️ Curating {destination}'s trendiest travel looks..."):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion editor for Condé Nast Traveler. Respond ONLY in the requested format."},
                    {"role": "user", "content": travel_prompt}
                ],
                max_tokens=400
            )
            result = response.choices[0].message.content.strip()
            
            st.success(f"🧿 {destination} Travel Style Guide")
            st.caption(f"Perfect for {trip_type} trips during {travel_season} | Age: {travel_age}")

            if "Women:" in result and "Men:" in result:
                women_trends, men_trends = result.split("Men:")
                
                # Women's Section
                st.subheader("👩 Women's Picks")
                for line in women_trends.replace("Women:", "").strip().split('\n'):
                    if line.strip():
                        st.markdown(f"""
                        <div class='trend-item' style='border-left: 3px solid #fbc2eb;'>
                        {line.strip()}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Men's Section
                st.subheader("👨 Men's Picks")
                for line in men_trends.strip().split('\n'):
                    if line.strip():
                        st.markdown(f"""
                        <div class='trend-item' style='border-left: 3px solid #a1c4fd;'>
                        {line.strip()}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='trend-item'>
                {result}
                </div>
                """, unsafe_allow_html=True)
# ---------- Tab 3: Fashion Trends ----------
with tab3:
    st.header("🧵 Fashion Trends")
    region = st.selectbox("🌍 Select Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"], key="region3")

    if st.button("📊 Show Trends"):
        trend_prompt = (
            f"You are a fashion trends expert. Provide concise, emoji-rich trend reports.\n"
            f"Include sections like Women: and Men:\n"
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

            st.success(f"🧥 Current Trends in {region}")

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
