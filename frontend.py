import openai
import streamlit as st
import requests
from PIL import Image
import io
import time

openai.api_key = st.secrets["OPENAI_API_KEY"]

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

# ---------- Meta Tags (for preview and SEO) ----------
st.markdown("""
    <meta name="title" content="StyleSync – AI Fashion Assistant">
    <meta name="description" content="Upload your clothing image and get personalized outfit suggestions using AI.">
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
    2. Select **Occasion**, **Season**, and **Age Group**.
    3. AI will generate a **matching outfit suggestion**.
    4. Download your personalized suggestion!
    """)

with st.sidebar.expander("🧠 What is Style Memory?"):
    st.markdown("""
    Style Memory keeps track of outfits you've uploaded in the session. 
    It helps recommend new combinations based on what you've already added.
    """)

st.sidebar.markdown("""
📱 *iPhone users: For best results, please use Safari browser to upload images directly from the camera.*
""")
