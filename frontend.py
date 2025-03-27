import openai
import streamlit as st
import requests
from PIL import Image
import io
import time

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------- Custom Welcome Page (Only show once) ----------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome:
    st.set_page_config(page_title="StyleSync", layout="wide")
    st.markdown(
        """
        <div style='background: linear-gradient(to right, #a18cd1, #fbc2eb);
                    height:100vh; display:flex; flex-direction:column;
                    justify-content:center; align-items:center;
                    color: white; text-align:center;'>
            <h1 style='font-size: 4rem; margin-bottom: 0;'>Welcome to StyleSync</h1>
            <p style='font-size: 1.5rem;'>Your AI-powered clothing assistant</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    time.sleep(5)
    st.session_state.show_welcome = False
    st.rerun()

# ---------- Custom CSS ----------
st.markdown("""
    <style>
        .stApp {
            background-color: #f0f8ff;
            padding: 2rem;
        }
        .css-18ni7ap.e8zbici2 {
            color: #003366;
            text-align: center;
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

with st.sidebar.expander("ℹ️ How It Works"):
    st.markdown("""
    1. **Upload** an image of your clothing item (shirt, dress, etc.) using camera or gallery.
    2. Select **Occasion**, **Season**, and **Age Group**.
    3. Our AI will generate a **matching outfit suggestion**.
    4. Download your personalized suggestion if you'd like!
    """)

with st.sidebar.expander("🧠 What is Style Memory?"):
    st.markdown("""
    Style Memory keeps track of outfits you've uploaded in the session. 
    It helps recommend new combinations based on what you've already added to your wardrobe.
    """)

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Fashion Assistant"])

# ---------- Outfit Suggestion Tab ----------
with tab1:
    st.markdown("<h1 style='text-align: center;'>👕 AI Fashion Outfit Suggestions</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload an image or take a photo, and AI will suggest a matching outfit in seconds!</p>", unsafe_allow_html=True)

    occasion = st.selectbox("👗 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
    season = st.selectbox("☀️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])
    age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
    style_memory_enabled = st.toggle("🧠 Enable Style Memory", value=False)

    uploaded_file = st.file_uploader("Choose an image or take a photo...", type=["jpg", "jpeg", "png"])

    st.markdown("_Tip: On mobile, tap 'Choose file' to either upload from gallery or take a photo using your camera._")

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        image = image.resize((500, 500))
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)

        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG", quality=70)
        img_bytes.seek(0)

        data = {
            "occasion": occasion,
            "season": season,
            "age": age
        }

        files = {
            'file': ('resized.jpg', img_bytes, 'image/jpeg')
        }

        with st.spinner("Analyzing outfit... Please wait..."):
            try:
                response = requests.post(
                    "https://stylesync-backend-2kz6.onrender.com/upload",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()
                    suggestion = result["fashion_suggestion"]
                    st.success("✅ AI Suggestion:")
                    st.markdown(suggestion)

                    st.download_button(
                        label="📥 Download Suggestion",
                        data=suggestion,
                        file_name="style_suggestion.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"❌ Exception occurred: {e}")

        if style_memory_enabled:
            if "style_memory" not in st.session_state:
                st.session_state.style_memory = []
            st.session_state.style_memory.append(image)

            st.markdown("<h3>🧠 Style Memory (Your Uploaded Wardrobe)</h3>", unsafe_allow_html=True)
            for img in st.session_state.style_memory:
                st.image(img, width=200)

# ---------- Travel Fashion Assistant Tab ----------
with tab2:
    st.markdown("<h2>✈️ Travel Fashion Assistant</h2>", unsafe_allow_html=True)
    with st.form("travel_form"):
        st.markdown("Get outfit and packing suggestions for your next trip!")
        destination = st.text_input("🌍 Destination", placeholder="e.g. Istanbul")
        travel_season = st.selectbox("🗓️ Season", ["Spring", "Summer", "Autumn", "Winter"])
        trip_type = st.selectbox("💼 Trip Type", ["Casual", "Business", "Wedding", "Adventure"])
        age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
        submitted = st.form_submit_button("Get Travel Suggestions")

        if submitted and destination:
            travel_prompt = (
                f"I'm going on a {trip_type.lower()} trip to {destination} in {travel_season}. "
                f"I am in my {age}. Please suggest appropriate outfits and a packing list."
            )

            with st.spinner("🧳 Planning your stylish trip..."):
                try:
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4",
                            "messages": [
                                {"role": "system", "content": "You are a travel fashion stylist. Give weather-appropriate outfit and packing suggestions."},
                                {"role": "user", "content": travel_prompt}
                            ],
                            "max_tokens": 400
                        }
                    )

                    if response.status_code == 200:
                        travel_suggestion = response.json()["choices"][0]["message"]["content"]
                        st.success("✅ Travel Style Suggestion:")
                        st.markdown(travel_suggestion)
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")

                except Exception as e:
                    st.error(f"❌ Exception: {e}")
