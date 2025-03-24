import streamlit as st
import requests
from PIL import Image
import io

# ---------- Custom CSS ----------
st.markdown("""
    <style>
        .stApp {
            background-color: #f0f8ff;
            padding: 2rem;
        }

        .css-18ni7ap.e8zbici2 {  /* Main title */
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

# ---------- Main UI ----------
st.markdown("<h1 style='text-align: center;'>👕 AI Fashion Outfit Suggestions</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload an image, and AI will suggest a matching outfit in seconds!</p>", unsafe_allow_html=True)

# ---------- Filters ----------
occasion = st.selectbox("👗 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
season = st.selectbox("☀️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])

# ---------- Image Upload ----------
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((500, 500))
    st.image(image, caption="📸 Uploaded Image", use_container_width=True)

    # Convert image to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=70)
    img_bytes.seek(0)

    # Data and file to send to backend
    data = {
        "occasion": occasion,
        "season": season
    }

    files = {
        'file': ('resized.jpg', img_bytes, 'image/jpeg')
    }

    # ---------- Send to backend ----------
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

                # ✅ Download button
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
