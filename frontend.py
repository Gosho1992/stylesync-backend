import openai
import streamlit as st
import requests
from PIL import Image
import io

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------- Session State for Style Memory ----------
if "wardrobe" not in st.session_state:
    st.session_state.wardrobe = []

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

# ---------- How It Works ----------
with st.sidebar.expander("ℹ️ How It Works"):
    st.markdown("""
    1. **Upload** an image of your clothing item (shirt, dress, etc.).
    2. Select the **Occasion** and **Season**.
    3. Toggle **Style Memory** ON to store the item temporarily.
    4. Our AI (powered by GPT-4) will generate a **matching outfit suggestion**.
    5. Download your personalized suggestion if you'd like!
    """)
# Style Memory - Expander
with st.sidebar.expander("🧠 What is Style Memory?"):
    st.markdown("""
    Style Memory lets you build your own mini-closet! 👗👔

    Here's how it works:
    1. **Upload** a clothing item and get outfit suggestions.
    2. Click **"💾 Save to Style Memory"** to store the item temporarily.
    3. Upload more items and build your wardrobe.
    4. Click **"🧠 Suggest from My Style Memory"** to get a full outfit based on your saved items!

    Style Memory is **session-based**, meaning it resets when you refresh the page.
    """)

# ---------- Main UI ----------
st.markdown("<h1 style='text-align: center;'>👕 AI Fashion Outfit Suggestions</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload an image, and AI will suggest a matching outfit in seconds!</p>", unsafe_allow_html=True)

# ---------- Filters ----------
occasion = st.selectbox("👗 Occasion", ["Casual", "Formal", "Party", "Wedding", "Work"])
season = st.selectbox("☀️ Season", ["Any", "Summer", "Winter", "Spring", "Autumn"])

# ---------- Style Memory Toggle ----------
style_memory = st.toggle("🧠 Enable Style Memory", value=False)

# ---------- Image Upload ----------
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((500, 500))
    st.image(image, caption="📸 Uploaded Image", use_container_width=True)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=70)
    img_bytes.seek(0)

    data = {
        "occasion": occasion,
        "season": season
    }

    files = {
        'file': ('resized.jpg', img_bytes, 'image/jpeg')
    }

    if style_memory:
        st.session_state.wardrobe.append(image)

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

# ---------- Travel Fashion Assistant ----------
st.markdown("---")
st.markdown("<h3>✈️ Travel Fashion Assistant</h3>", unsafe_allow_html=True)

with st.form("travel_form"):
    st.markdown("Get outfit and packing suggestions for your next trip!")

    destination = st.text_input("🌍 Destination", placeholder="e.g. Istanbul")
    travel_season = st.selectbox("🗓️ Season", ["Spring", "Summer", "Autumn", "Winter"])
    trip_type = st.selectbox("💼 Trip Type", ["Casual", "Business", "Wedding", "Adventure"])

    submitted = st.form_submit_button("Get Travel Suggestions")

    if submitted and destination:
        travel_prompt = (
            f"I'm going on a {trip_type.lower()} trip to {destination} in {travel_season}. "
            f"Please suggest appropriate outfits and a packing list."
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

# ---------- View Style Memory ----------
if style_memory and st.session_state.wardrobe:
    st.markdown("---")
    st.markdown("<h3>🧠 Style Memory (Your Uploaded Wardrobe)</h3>", unsafe_allow_html=True)
    for idx, img in enumerate(st.session_state.wardrobe):
        st.image(img, caption=f"Saved Look #{idx+1}", use_container_width=True)
