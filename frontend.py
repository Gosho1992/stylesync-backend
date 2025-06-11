# ✅ Corrected frontend.py with all name updates from StyleSync → StyleWithAI
from openai import OpenAI
import streamlit as st
import requests
from PIL import Image
from gtts import gTTS
from deep_translator import GoogleTranslator
import io
import time
from textwrap import wrap
import re
import base64
from dotenv import load_dotenv
import os
from streamlit.components.v1 import html
import stripe
import requests

# Initialize environment first
load_dotenv()

st.set_page_config(page_title="StyleWithAI", layout="wide")


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Do not hardcode key!

STRIPE_PRICE_ID = "price_1RYNCkB1g7uD1vIapFF9HOwr"
SUCCESS_URL = "https://gosho1992-stylesync-backend-frontend-0zlcqx.streamlit.app/"
API_URL = "https://stylesync-backend-2kz6.onrender.com/check-premium"


# ----- Helper Functions -----
def img_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def translate_long_text(text, target_lang):
    chunks = wrap(text, width=4500)
    translated_chunks = [
        GoogleTranslator(source='auto', target=target_lang).translate(chunk)
        for chunk in chunks
    ]
    return "\n\n".join(translated_chunks)

def format_text_block(text):
    sections = re.split(r'\n\d+\.', text)
    if len(sections) > 1:
        formatted = ""
        for i, section in enumerate(sections[1:], 1):
            section = section.strip()
            if not section:
                continue
            emoji = get_section_emoji(section)
            formatted += f"\n{emoji} **{i}. {section.split('.')[0].strip()}**\n"
            points = [p.strip() for p in section.split('.')[1:] if p.strip()]
            for point in points[:3]:
                formatted += f"   ◦ {point}\n"
            formatted += "\n"
        return formatted

    paragraphs = text.split("\n")
    formatted = ""
    current_section = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.endswith(":") or any(word in p.lower() for word in [
            "outfit", "attire", "accessories", "daywear", "nightwear", "tips", 
            "shoes", "summary", "jewelry", "temple", "trends", "men", "women"]):
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
        return "💼"
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

def render_style_card(store, products, price_range):
    st.markdown(f"""
    <div style='
        background: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #bb377d;
    '>
        <h4 style='margin:0; color: #bb377d;'>{store}</h4>
        <p style='margin:5px 0;'>{products}</p>
        <p style='margin:0; font-size:0.9em; color:#666;'>{price_range}</p>
    </div>
    """, unsafe_allow_html=True)

# ----- Initialize APIs -----
# Get API key from secrets or environment
openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

if not openai_api_key:
    st.error("OpenAI API key not found! Check your environment variables or secrets.")
    st.stop()

client = OpenAI(api_key=openai_api_key)


# ---------- Welcome Splash ----------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome:
    st.markdown("""
        <div style='background: linear-gradient(to right, #fbd3e9, #bb377d);
                    height:100vh; display:flex; flex-direction:column;
                    justify-content:center; align-items:center;
                    color: white; text-align:center;'>
            <h1 style='font-size: 4rem;'>Welcome to StyleWithAI</h1>
            <p style='font-size: 1.5rem;'>Your AI-powered clothing assistant</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.show_welcome = False
    st.rerun()

# ---------- CSS Styling ----------
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
st.sidebar.image("assets/stylewithai_logo.png", width=100)
st.sidebar.title("👗 StyleWithAI")
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
tab1, tab2, tab3, tab4 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Assistant", "📊 Trends", "AI Mirror of Truth"])

# ---------- Tab 1: Outfit Suggestion ----------
with tab1:
    st.header("👗 Personal Style Architect")

    # Persist selections
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "suggestion" not in st.session_state:
        st.session_state.suggestion = ""
    if "translated_suggestion" not in st.session_state:
        st.session_state.translated_suggestion = ""

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
    uploaded_file = st.file_uploader(
        "📸 Upload Your Style Canvas", 
        type=["jpg", "jpeg", "png"],
        help="For best results, use well-lit front-facing images"
    )
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file:
        st.image(Image.open(st.session_state.uploaded_file), caption="🎨 Your Style Foundation", width=300)

    # Generate button
    if st.button("✨ Generate Masterpiece", type="primary", use_container_width=True):
        if not st.session_state.uploaded_file:
            st.warning("⚠️ Please upload an image before generating your masterpiece.")
        else:
            data = {
                "occasion": occasion,
                "season": season,
                "gender": gender,
                "body_type": body_type,
                "age": age,
                "mood": mood,
                "format_instructions": """Respond in Markdown with:
                ## [Theme Name]
                - **Vibe**: [Mood descriptor]
                - **Top**: [Item] + [Details]
                - **Bottom**: [Item] + [Fit Note]
                - **Shoes**: [Type] + [Seasonal Advice]
                - **Accents**: 3 items with benefits
                - **Fit Hack**: [Body-type specific tip]"""
            }

            with st.spinner("🎨 Crafting your couture vision..."):
                try:
                    response = requests.post(
                        "https://stylesync-backend-2kz6.onrender.com/upload",
                        files={'file': ('image.jpg', st.session_state.uploaded_file.getvalue(), 'image/jpeg')},
                        data=data,
                        timeout=20
                    )

                    if response.status_code == 200:
                        st.session_state.suggestion = response.json().get("fashion_suggestion", "")
                        st.session_state.translated_suggestion = ""
                        st.session_state.image_prompt = response.json().get("image_prompt", "")  # Store image prompt

                        if not st.session_state.suggestion:
                            st.error("🎭 Our stylists need more inspiration! Try again.")
                        else:
                            st.balloons()
                            st.success("🌟 Style Masterpiece Completed!")

                    else:
                        st.error(f"⚠️ Creative Block (Error {response.status_code})")

                except requests.exceptions.RequestException:
                    st.error("🌐 Connection Error: The fashion universe is unreachable")
                except Exception as e:
                    st.error(f"🎭 Unexpected Artistry Failure: {str(e)}")

    # Output
    if st.session_state.suggestion:
        if lang_codes[language_option] != "en":
            if not st.session_state.translated_suggestion:
                st.session_state.translated_suggestion = translate_long_text(
                    st.session_state.suggestion,
                    lang_codes[language_option]
                )
            display_text = st.session_state.translated_suggestion
        else:
            display_text = st.session_state.suggestion

        st.markdown("### ✨ Your Style Masterpiece")
        st.markdown("---")
        st.markdown(display_text)
        st.markdown("---")

        with st.expander("🔍 Style Breakdown", expanded=False):
            st.table({
                "Filter": ["Gender", "Body Type", "Age", "Mood", "Occasion", "Season"],
                "Applied Value": [gender, body_type, age, mood, occasion, season]
            })

        if st.button("🎧 Hear Your Style Story"):
            with st.spinner("Composing your fashion sonnet..."):
                tts = gTTS(text=st.session_state.suggestion, lang=lang_codes[language_option])
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                st.audio(audio_bytes, format="audio/mp3")

# ---------- Tab 2: Travel Assistant ----------
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

        with st.spinner(f"✈️ Researching fashion norms for {destination}..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a concise travel fashion advisor. Use bullet points, emojis, and keep suggestions very brief."},
                    {"role": "user", "content": travel_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])
            
            st.success(f"🧳 {destination} Travel Style Guide")
            st.caption(f"Perfect for {trip_type} trips during {travel_season} | Age: {travel_age}")

            if "Women:" in translated and "Men:" in translated:
                women_trends, men_trends = translated.split("Men:")
                
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
                {translated}
                </div>
                """, unsafe_allow_html=True)

# ---------- Tab 3: Fashion Trends ----------
with tab3:
    st.header("📊 Current Fashion Trends")
    st.markdown("Discover what's trending around the world")
    
    region = st.selectbox("🌍 Select Region", ["Global", "Pakistan", "India", "USA", "Europe", "Middle East"], key="region3")
    
    if st.button("👀 Show Current Trends", key="trends_btn"):
        trend_prompt = (
            f"You are a fashion trends expert. Provide concise, emoji-rich trend reports.\n"
            f"Include sections like Women: and Men:\n"
            f"Add relevant emojis and separate by gender.\n"
            f"Keep each trend to one line maximum."
        )

        with st.spinner(f"🔍 Analyzing {region} fashion trends..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion trends expert. Provide concise, emoji-rich trend reports."},
                    {"role": "user", "content": trend_prompt}
                ],
                max_tokens=600
            )
            result = response.choices[0].message.content.strip()
            translated = translate_long_text(result, lang_codes[language_option])

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

with tab4:
    st.header("✨ AI Mirror of Truth – Premium Experience")
    
    # ========== INITIALIZATION ==========
    # Initialize session state variables
    if "premium_unlocked" not in st.session_state:
        st.session_state.premium_unlocked = False
    if "stripe_link" not in st.session_state:
        st.session_state.stripe_link = None
    if "payment_checked" not in st.session_state:
        st.session_state.payment_checked = False
    
    # ========== PAYMENT CONFIG CHECK ==========
    if not stripe.api_key:
        st.error("""
        ⚠️ Payment system not configured properly. 
        Please contact support or try again later.
        """)
        st.stop()
    
    # ========== USER INPUT SECTION ==========
    with st.form("premium_access_form"):
        email = st.text_input("✉️ Email Address*", help="Required for payment receipt and access")
        name = st.text_input("👤 Your Name (Optional)")
        submitted = st.form_submit_button("Check Premium Status")
        
        if submitted:
            if not email:
                st.warning("Please enter your email address")
            else:
                st.session_state.payment_checked = False
    
    # ========== PAYMENT STATUS CHECK ==========
    if email and not st.session_state.premium_unlocked and not st.session_state.payment_checked:
        with st.spinner("🔍 Verifying your premium access..."):
            try:
                # Call your backend API to check payment status
                response = requests.get(
                    API_URL,
                    params={"email": email.strip().lower()},
                    timeout=10
                )
                
                if response.status_code == 200:
                    user_data = response.json()

                    # DEBUG PRINTS
                    st.write("DEBUG: user_data from API →", user_data)
                    st.write("DEBUG: email entered →", email.strip().lower())

                    if isinstance(user_data, list):
                        user_record = next(
                            (
                                u for u in user_data
                                if u.get("email", "")
                                    .strip()
                                    .lower()
                                    .replace('\u00a0', '')  # non-breaking space
                                    .replace(' ', '')       # remove spaces
                                ==
                                email.strip().lower()
                                    .replace('\u00a0', '')
                                    .replace(' ', '')
                            ),
                            None
                        )
                    else:
                        user_record = user_data
                    
                    if user_record and user_record.get("status", "").strip().lower() == "paid":
                        st.session_state.premium_unlocked = True
                        st.success("🎉 Premium access granted! Loading your features...")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("🔒 Premium features not yet unlocked for this email")
                else:
                    st.warning("⚠️ Couldn't verify payment status. Please try again later.")
                
            except requests.exceptions.RequestException:
                st.error("🚫 Connection error. Please check your internet and try again")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
            
            st.session_state.payment_checked = True

    # ========== PREMIUM CONTENT (UNLOCKED) ==========
    if st.session_state.premium_unlocked:
        st.success("""
        💎 **Premium Features Unlocked!**  
        Enjoy your enhanced fashion experience.
        """)

        
        # Create tabs for premium features
        tab_roast, tab_glowup, tab_diagnostic = st.tabs([
            "🔥 Brutal Roast", 
            "💎 Glow-Up Plan", 
            "🔍 Full Diagnostic"
        ])
        
        # --- Brutal Roast Tab ---
        with tab_roast:
            st.subheader("💋 Outfit Roast Me")
            with st.expander("📸 Upload Your Outfit", expanded=True):
                roast_img = st.file_uploader(
                    "Upload that questionable outfit...",
                    type=["jpg", "jpeg", "png"],
                    key="roast_upload"
                )
                
                if roast_img and st.button("🔥 Roast My Outfit"):
                    with st.spinner("Gathering the fashion police..."):
                        try:
                            img = Image.open(roast_img)
                            img_b64 = img_to_base64(img)
                            
                            ROAST_PROMPT = """You're a fashionista with *opinions*. Give a flirty, shady-but-loving roast..."""
                            
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": ROAST_PROMPT},
                                    {
                                        "role": "user", 
                                        "content": [
                                            {"type": "text", "text": "Roast this outfit"},
                                            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                                        ]
                                    }
                                ]
                            )
                            
                            st.markdown(f"""
                            <div style='
                                background:#FFF0F5;
                                padding:20px;
                                border-radius:12px;
                                border-left:5px solid #FF69B4;
                            '>
                                <h4 style='color:#FF1493;'>💅 Fashion Police Verdict</h4>
                                {response.choices[0].message.content}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Failed to generate roast: {str(e)}")
        
        # --- Glow-Up Plan Tab ---
        with tab_glowup:
            st.subheader("💎 Personal Stylist Review")
            # ... [similar implementation as roast tab] ...
        
        # --- Full Diagnostic Tab ---
        with tab_diagnostic:
            st.subheader("🔍 Comprehensive Style Analysis")
            # ... [similar implementation] ...

    # ========== PAYMENT FLOW (LOCKED) ==========
    else:
        st.markdown("""
        ## 🔒 Premium Features Include:
        - **AI Outfit Roasting** - Get brutally honest feedback
        - **Personal Glow-Up Plans** - Customized style roadmaps  
        - **Full Style Diagnostics** - Head-to-toe analysis
        """)
        
        st.warning("""
        💡 Requires one-time $5 payment. 
        After payment, refresh this page to access features.
        """)
        
        # Display payment link if generated
        if st.session_state.stripe_link:
            st.markdown(f"""
            <div style='
                background:#f8f9fa;
                padding:20px;
                border-radius:10px;
                border-left:4px solid #0066cc;
                margin-bottom:20px;
            '>
                <h4 style='margin-top:0;'>💳 Payment Ready</h4>
                <a href='{st.session_state.stripe_link}' target='_blank'>
                    <button style='
                        background:#0066cc;
                        color:white;
                        border:none;
                        padding:12px 24px;
                        border-radius:6px;
                        font-size:16px;
                        cursor:pointer;
                    '>Complete Payment Now</button>
                </a>
                <p><small>Secure payment via Stripe • Cancel anytime</small></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Payment initiation button
        if st.button("👉 Unlock Premium for $5", type="primary", use_container_width=True):
            if not email:
                st.warning("Please enter your email first")
            else:
                with st.spinner("Creating secure payment link..."):
                    try:
                        checkout_session = stripe.checkout.Session.create(
                            payment_method_types=["card"],
                            line_items=[{
                                "price": STRIPE_PRICE_ID,
                                "quantity": 1,
                            }],
                            mode="payment",
                            customer_email=email,
                            success_url=SUCCESS_URL,
                            cancel_url=SUCCESS_URL,
                            metadata={
                                "email": email,
                                "name": name or "Anonymous"
                            }
                        )
                        st.session_state.stripe_link = checkout_session.url
                        st.rerun()
                    except stripe.error.StripeError as e:
                        st.error(f"Payment error: {e.user_message}")
                    except Exception as e:
                        st.error(f"System error: {str(e)}")
        
        # Help section
        with st.expander("ℹ️ Need Help?", expanded=False):
            st.markdown("""
            **How to unlock premium:**
            1. Enter your email above
            2. Click "Unlock Premium for $5"
            3. Complete payment on Stripe
            4. Return here and refresh the page
            
            **Test Card:** `4242 4242 4242 4242`  
            **Contact:** support@stylewithai.com
            """)