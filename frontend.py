# ✅ Corrected frontend.py with all name updates from StyleSync → StyleWithAI
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

st.set_page_config(page_title="StyleWithAI", layout="wide")

# ---------- Welcome Splash (Once per session) ----------
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
    time.sleep(5)
    st.session_state.show_welcome = False
    st.rerun()

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        color: black !important;
    }

    div[data-testid="stMarkdownContainer"] {
        color: black !important;
    }

    h1, h2, h3, h4, h5, h6, p, span {
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

openai.api_key = st.secrets["OPENAI_API_KEY"]


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
st.sidebar.title("👗 Stylewithai")
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
tab1, tab2, tab3 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Assistant", "📊 Trends"])
with tab1:
    st.header("👗 Personal Style Architect")

    from PIL import Image
    import io

    # ---------- Style Filters ----------
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

    # ---------- File Upload ----------
    uploaded_file = st.file_uploader("📸 Upload Your Style Canvas", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        try:
            image_data = uploaded_file.getvalue()
            img = Image.open(io.BytesIO(image_data))
            st.image(img, caption="🎨 Your Style Foundation", use_container_width=True)
        except Exception as e:
            st.error(f"🚫 Error loading image: {str(e)}")

    # ---------- Session States ----------
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "suggestion" not in st.session_state:
        st.session_state.suggestion = ""
    if "translated_suggestion" not in st.session_state:
        st.session_state.translated_suggestion = ""
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = []
    if "outfit_categories" not in st.session_state:
        st.session_state.outfit_categories = {}

    # ---------- Submit to Backend ----------
    if st.button("✨ Generate Masterpiece", type="primary", use_container_width=True):
        if not st.session_state.uploaded_file:
            st.warning("⚠️ Please upload an image before generating your masterpiece.")
        else:
            st.session_state.generated_images = []
            st.session_state.outfit_categories = {}

            data = {
                "occasion": occasion,
                "season": season,
                "gender": gender,
                "body_type": body_type,
                "age": age,
                "mood": mood
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
                        if not st.session_state.suggestion:
                            st.error("🎭 Our stylists need more inspiration! Try again.")
                        else:
                            st.balloons()
                            st.success("🌟 Style Masterpiece Completed!")
                            st.rerun()
                    else:
                        st.error(f"⚠️ Error {response.status_code}")
                except requests.exceptions.RequestException:
                    st.error("🌐 Network error: Unable to reach the style server.")
                except Exception as e:
                    st.error(f"🎭 Unexpected error: {str(e)}")

    # ---------- Display AI Suggestion ----------
    if st.session_state.suggestion:
        st.markdown("### ✨ Your Style Masterpiece")
        st.markdown("---")
        st.markdown(st.session_state.suggestion)
        st.markdown("---")

    # ---------- 🧠 Outfit Visual Board ----------
    if st.session_state.suggestion:
        st.markdown("## 🖼️ Outfit Visualization")
        st.caption("AI-generated product images of recommended clothing and accessories")

        import re
        import requests
        import openai
        openai.api_key = st.secrets["OPENAI_API_KEY"]

        def categorize_items(item_text):
            """Categorize items into footwear, accessories, etc."""
            item_lower = item_text.lower()
            if any(word in item_lower for word in ['shoe', 'boot', 'sandal', 'loafer', 'sneaker']):
                return "Footwear"
            elif any(word in item_lower for word in ['watch', 'sunglass', 'bag', 'hat', 'belt', 'scarf']):
                return "Accessories"
            elif any(word in item_lower for word in ['shirt', 'blouse', 'top', 't-shirt']):
                return "Tops"
            elif any(word in item_lower for word in ['pant', 'jean', 'skirt', 'short']):
                return "Bottoms"
            elif any(word in item_lower for word in ['dress', 'jumpsuit']):
                return "Dresses"
            elif any(word in item_lower for word in ['jacket', 'coat', 'blazer', 'sweater']):
                return "Outerwear"
            return "Other"

        def parse_outfit_items(markdown_text):
            items = []
            categories = {}
            
            # Try multiple patterns to extract items
            patterns = [
                r"\d+\.\s+\*\*(.*?)\*\*:\s*(.*)",  # **Label**: Item
                r"\d+\.\s+\*\*(.*)\*\*",           # **Item**
                r"\d+\.\s+(.*)",                    # 1. Item
                r"- \*\*(.*)\*\*",                  # - **Item**
                r"- (.*)"                           # - Item
            ]
            
            for pattern in patterns:
                for match in re.findall(pattern, markdown_text):
                    if isinstance(match, tuple):
                        item = match[-1].strip()  # Take the last group in case of multiple capture groups
                    else:
                        item = match.strip()
                    
                    if item and len(item) < 100:  # Reasonable length check
                        items.append(item)
                        item_category = categorize_items(item)
                        if item_category not in categories:
                            categories[item_category] = []
                        if item not in categories[item_category]:  # Avoid duplicates
                            categories[item_category].append(item)

            # Fallback: If no items found with patterns, look for lines that might contain items
            if not items:
                for line in markdown_text.split('\n'):
                    clean_line = line.strip().lstrip('-').lstrip('*').strip()
                    if clean_line and len(clean_line) < 100 and not clean_line.startswith(('**', '#', '---')):
                        items.append(clean_line)
                        item_category = categorize_items(clean_line)
                        if item_category not in categories:
                            categories[item_category] = []
                        if clean_line not in categories[item_category]:
                            categories[item_category].append(clean_line)

            st.session_state.outfit_categories = categories
            return list(set(items))[:6]  # Return up to 6 unique items

        def generate_dalle_image(prompt):
            try:
                response = openai.images.generate(
                    model="dall-e-3",
                    prompt=f"Professional product photo of {prompt}, isolated on white background, studio lighting, high detail, e-commerce style, 4k",
                    n=1,
                    size="1024x1024",
                    quality="standard"
                )
                return response.data[0].url
            except Exception as e:
                st.error(f"❌ Failed to generate image for {prompt}: {str(e)}")
                return None

        if not st.session_state.generated_images:
            outfit_items = parse_outfit_items(st.session_state.suggestion)
            
            if not outfit_items:
                st.warning("🔍 Couldn't identify specific fashion items in the recommendation. Trying alternative approach...")
                # Try to extract the most noun-like phrases
                nouns = re.findall(r'\b[A-Z][a-z]+\b(?: \b[A-Z][a-z]+\b)*', st.session_state.suggestion)
                outfit_items = list(set([n for n in nouns if len(n.split()) <= 3 and len(n) > 3][:4]))
            
            if outfit_items:
                with st.spinner("🧵 Generating visuals for your outfit..."):
                    progress = st.progress(0)
                    for i, item in enumerate(outfit_items):
                        url = generate_dalle_image(item)
                        if url:
                            st.session_state.generated_images.append((item, url))
                        progress.progress((i + 1) / len(outfit_items))
                    progress.empty()
            else:
                st.error("❌ Couldn't extract any fashion items to visualize. Please try generating again.")

        if st.session_state.generated_images:
            # Display by categories if we have them
            if st.session_state.outfit_categories:
                for category, items in st.session_state.outfit_categories.items():
                    if items:  # Only show categories that have items
                        st.subheader(f"{category}")
                        cols = st.columns(min(3, len(items)))
                        for idx, item in enumerate(items):
                            # Find the matching image URL
                            img_url = next((url for (itm, url) in st.session_state.generated_images if itm.lower() == item.lower()), None)
                            if img_url:
                                with cols[idx % len(cols)]:
                                    st.image(img_url, caption=item, use_container_width=True)
            else:
                # Fallback to original display if no categories
                cols = st.columns(2)
                for idx, (item, url) in enumerate(st.session_state.generated_images):
                    with cols[idx % 2]:
                        st.image(url, caption=item, use_container_width=True)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔁 Regenerate Images Only", help="Regenerate the visualizations without changing the outfit recommendations"):
                    st.session_state.generated_images = []
                    st.rerun()
            with col2:
                if st.button("🔄 Generate New Outfit", type="primary"):
                    st.session_state.suggestion = ""
                    st.session_state.generated_images = []
                    st.session_state.outfit_categories = {}
                    st.rerun()

            if st.button("💾 Download All Outfit Images"):
                for i, (item, url) in enumerate(st.session_state.generated_images):
                    try:
                        img_data = requests.get(url).content
                        st.download_button(
                            label=f"Download {item}",
                            data=img_data,
                            file_name=f"{item.replace(' ', '_').lower()}.png",
                            mime="image/png",
                            key=f"dl_{i}"
                        )
                    except Exception as e:
                        st.error(f"Download failed for {item}: {str(e)}")
        elif st.session_state.suggestion and not st.session_state.generated_images:
            st.warning("No outfit visuals could be generated from the recommendation. Try regenerating.")
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