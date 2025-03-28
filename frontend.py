import streamlit as st
import requests
from gtts import gTTS
import os
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="StyleSync AI", page_icon="👗", layout="wide")

# Session state for style memory
if "wardrobe" not in st.session_state:
    st.session_state["wardrobe"] = []

# Function to get outfit suggestion from backend
def get_outfit_suggestion(image_file):
    backend_url = "https://stylesync-backend.onrender.com/suggest"
    files = {"file": image_file}
    response = requests.post(backend_url, files=files)
    return response.json()

# Function for TTS
def play_tts(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.audio(fp.name, format="audio/mp3")

# Function for regional fashion trends (mocked)
def get_fashion_trends(region):
    trends = {
        "Pakistan": ["Shalwar Kameez revival", "Bold embroidery", "Pastel tones"],
        "Europe": ["Layered trench coats", "Minimalist chic", "Sustainable denim"],
        "USA": ["Streetwear influence", "Y2K styles", "Bold accessories"]
    }
    return trends.get(region, ["No trends available"])

# Sidebar
with st.sidebar:
    st.image("https://i.ibb.co/ZxR92dd/stylesync-logo.png", width=120)
    st.markdown("### 👗 StyleSync AI")
    st.markdown("Your AI-powered fashion assistant 🧵")
    st.markdown("Upload your clothing item and get matching outfit suggestions powered by GPT-4.")
    st.markdown("Created by gosho1992 · [GitHub](https://github.com/gosho1992)")

# Tabs
tab1, tab2, tab3 = st.tabs(["👗 Outfit Suggestion", "🧳 Travel Fashion Assistant", "📰 Fashion Trends"])

# Tab 1: Outfit Suggestion
with tab1:
    st.subheader("Upload Your Clothing Item")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Item", use_column_width=True)

        if st.button("Get Outfit Suggestion"):
            with st.spinner("Analyzing and styling..."):
                result = get_outfit_suggestion(uploaded_file)
                suggestion = result.get("suggestion", "No suggestion received.")
                st.success(suggestion)

                # Add to wardrobe
                st.session_state["wardrobe"].append(suggestion)

                # TTS
                play_tts(suggestion)

    if st.session_state["wardrobe"]:
        st.markdown("### 👚 Your Style Memory")
        for item in st.session_state["wardrobe"]:
            st.markdown(f"- {item}")

# Tab 2: Travel Fashion Assistant
with tab2:
    st.subheader("Packing Assistant for Your Next Trip")
    region = st.selectbox("Where are you traveling?", ["Pakistan", "Europe", "USA"])
    days = st.slider("Trip duration (in days)", 1, 30, 7)

    if st.button("Generate Packing List"):
        st.markdown(f"### Packing suggestions for {region} ({days} days):")
        base_outfits = {
            "Pakistan": ["Light cotton clothes", "Shawl", "Sandals"],
            "Europe": ["Warm jacket", "Jeans", "Sneakers"],
            "USA": ["Graphic tees", "Hoodie", "Sneakers"]
        }
        for item in base_outfits.get(region, []):
            st.write(f"- {item} x{min(3, days // 3)}")

# Tab 3: Fashion Trends
with tab3:
    st.subheader("Latest Fashion Trends by Region")
    region = st.radio("Select Region", ["Pakistan", "Europe", "USA"], horizontal=True)
    trends = get_fashion_trends(region)

    st.markdown(f"### 🌍 Top Trends in {region}")
    for trend in trends:
        st.markdown(f"- {trend}")
