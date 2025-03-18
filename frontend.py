import streamlit as st
import requests

# Streamlit UI
st.title("👕 AI Fashion Outfit Suggestions")
st.write("Upload an image, and AI will suggest a matching outfit!")

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Display uploaded image
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    # Send image to Flask backend
    files = {"file": uploaded_file.getvalue()}
    response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files)

    # Display AI fashion suggestion
    if response.status_code == 200:
        result = response.json()
        st.success("✅ AI Suggestion:")
        st.write(result["fashion_suggestion"])
    else:
        st.error("❌ Error processing image!")
