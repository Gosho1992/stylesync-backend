import streamlit as st
import requests
from PIL import Image
import io
import time
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------- Welcome Splash (Once per session) ----------
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if st.session_state.show_welcome:
    st.set_page_config(page_title="StyleSync", layout="wide")
    st.markdown("""
        <div style='background: linear-gradient(to right, #a18cd1, #fbc2eb);
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

# ---------- Custom CSS ----------
st.markdown("""
    <style>
        .stApp { background-color: #f0f8ff; padding: 2rem; }
        .css-18ni7ap.e8zbici2 { color: #003366; text-align: center; }
        .stButton>button { background-color: #0066cc; color: white; padding: 0.5rem 1.5rem; border-radius: 8px; }
        .stMarkdown, .stImage {
            background-color: #ffffff; padding: 1rem;
            border-radius: 10px; box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.05);
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
    1. **Upload** an image of your clothing item (shirt, dress, etc.).
    2. Select **Occasion**, **Season**, **Age Group**, and **Gender**.
    3. AI will generate a **matching outfit suggestion**.
    4. Download your personalized suggestion!
    """)

with st.sidebar.expander("🧠 What is Style Memory?"):
    st.markdown("""
    Style Memory keeps track of outfits you've uploaded in the session. 
    It helps recommend new combinations based on what you've already added.
    """)

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["👕 Outfit Suggestion", "✈️ Travel Fashion Assistant", "🧵 Fashion Trends"])

# ---------- Outfit Suggestion Tab ----------
with tab1:
    st.markdown("<h1 style='text-align: center;'>👕 AI Fashion Outfit Suggestions</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload an image or take a photo, and AI will suggest a matching outfit!</p>", unsafe_allow_html=True)

    occasion = st.selectbox("👗 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
    season = st.selectbox("☀️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])
    age = st.selectbox("🎂 Age Group", ["Teen", "20s", "30s", "40s", "50+"])
    gender = st.selectbox("⚧️ Gender", ["Female", "Male", "Non-binary", "Genderfluid", "Agender", "Other"])
    custom_gender = ""
    if gender == "Other":
        custom_gender = st.text_input("Please specify your gender")

    final_gender = custom_gender if gender == "Other" else gender
    style_memory_enabled = st.toggle("🧠 Enable Style Memory", value=False)

    uploaded_file = st.file_uploader("Choose an image or take a photo...", type=["jpg", "jpeg", "png"])
    st.markdown("_Tip: On mobile, tap 'Choose file' to upload or take a photo. iPhone users should use Safari for best camera support._")

    if uploaded_file is not None:
        if uploaded_file.type.startswith("image/"):
            try:
                image = Image.open(uploaded_file).convert("RGB")
            except Exception:
                st.error("⚠️ Could not read the image. Try uploading from gallery instead.")
                st.stop()
        else:
            st.error("⚠️ Unsupported file type. Please upload JPG or PNG.")
            st.stop()

        image = image.resize((500, 500))
        st.image(image, caption="📸 Uploaded Image", use_container_width=True)

        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG", quality=70)
        img_bytes.seek(0)

        data = {
            "occasion": occasion,
            "season": season,
            "age": age,
            "gender": final_gender
        }
        files = { 'file': ('resized.jpg', img_bytes, 'image/jpeg') }

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
                    st.markdown(f"""
                    <div style='color:#222; font-size: 1.1rem; line-height: 1.6;'>
                    {suggestion}
                    </div>
                    """, unsafe_allow_html=True)

                    st.download_button("📥 Download Suggestion", suggestion, file_name="style_suggestion.txt", mime="text/plain")

                   if st.button("🧍 Generate Outfit Avatar"):
    with st.spinner("Creating avatar preview..."):
        try:
            dalle_prompt = f"Cartoon avatar wearing an outfit: {suggestion}. Show accessories if mentioned. Minimalist style."
            dalle_response = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            avatar_url = dalle_response.data[0].url
            st.image(avatar_url, caption="🧍 Outfit Avatar")
        except Exception as e:
            st.error(f"Error generating avatar: {e}")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

        if style_memory_enabled:
            if "style_memory" not in st.session_state:
                st.session_state.style_memory = []
            st.session_state.style_memory.append(image)

            st.markdown("<h3>🧠 Style Memory (Your Uploaded Wardrobe)</h3>", unsafe_allow_html=True)
            for img in st.session_state.style_memory:
                st.image(img, width=200)

    if st.button("🔄 Refresh App"):
        st.experimental_rerun()
