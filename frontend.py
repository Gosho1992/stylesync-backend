import streamlit as st
import requests
from PIL import Image
import io

# UI title
st.title("👕 AI Fashion Outfit Suggestions")
st.write("Upload an image, and AI will suggest a matching outfit!")

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Open and resize the image
    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((500, 500))

    # Display resized image
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Convert image to bytes buffer
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=70)
    img_bytes.seek(0)

    # Create file tuple in the correct format
    files = {'file': ('resized.jpg', img_bytes, 'image/jpeg')}

    # Send to backend
    try:
        response = requests.post("https://stylesync-backend-2kz6.onrender.com/upload", files=files)

        if response.status_code == 200:
            result = response.json()
            st.success("✅ AI Suggestion:")
            st.write(result["fashion_suggestion"])
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"❌ Exception occurred: {e}")
