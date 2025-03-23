import streamlit as st
import requests
from PIL import Image
import io

# Streamlit UI
st.title("👕 AI Fashion Outfit Suggestions")
st.write("Upload an image, and AI will suggest a matching outfit!")

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Open and resize the image using PIL
    image = Image.open(uploaded_file).convert("RGB")  # Convert to RGB just in case
    image = image.resize((500, 500))  # Resize to reduce upload time

    # Display resized image
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Compress and convert image to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=70)  # Compress image (lower quality = faster)
    img_bytes.seek(0)

    # Send compressed image to backend
    files = {"file": img_bytes.getvalue()}
    response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files)

    # Display AI fashion suggestion
    if response.status_code == 200:
        result = response.json()
        st.success("✅ AI Suggestion:")
        st.write(result["fashion_suggestion"])
    else:
        st.error(f"❌ Error {response.status_code}: Could not process the image.")
