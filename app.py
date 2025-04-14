from flask import Flask, request, jsonify 
import os
import base64
import openai
from werkzeug.utils import secure_filename

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("ERROR: OpenAI API key is missing. Set OPENAI_API_KEY in the environment.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize Flask app
app = Flask(__name__)

# Create a directory to store uploaded images
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Function to convert image to Base64
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

# Home route for testing
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "StyleSync Backend is Live!"})

# Upload endpoint
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Get additional form data
    occasion = request.form.get("occasion", "Any")
    season = request.form.get("season", "Any")
    age_group = request.form.get("age", "Any")
    mood = request.form.get("mood", "Neutral")
    region = request.form.get("region", "Global")

    # Save uploaded image
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Failed to process image"}), 500

    try:
        prompt = f"""
As Creative Director of a luxury fashion house, transform this single item into a head-to-toe look worthy of a Vogue editorial.

**Client Brief:**
- 📍 Location Influence: {region}-inspired details
- 🎯 Occasion: {occasion}-appropriate with a fashion-forward twist  
- 🌦️ Season: {season}-optimized fabrics and layering  
- 👑 Age: {age_group}-flattering silhouettes  
- 😌 Mood: {mood}-enhancing color psychology  

**Deliverables (Strict Markdown Format):**

**🖤 Signature Look:**  
*(1-line theme summary)*  

**🔍 Style Breakdown:**  
- **Top:** [Designer-inspired pairing] + [fabric detail]  
- **Bottoms:** [Trend-aware bottom] + [styling tip]  
- **Shoes:** [Seasonal statement footwear] + [functional note]  
- **Outerwear:** [Weather-appropriate topper] + [cultural nod]  
- **Accessories:**  
  - [Signature piece]  
  - [Functional add-on]  
  - [Trend accent]  

**💎 Pro Secret:**  
*(1 insider tip)*  

**✨ Final Note:**  
*(Mood-boosting affirmation)*
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fashion expert. Give stylish and practical fashion suggestions."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000
        )

        fashion_advice = response.choices[0].message.content

        return jsonify({
            "message": "Image uploaded successfully",
            "filename": filename,
            "fashion_suggestion": fashion_advice
        })

    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return jsonify({"error": "Failed to get response from OpenAI", "details": str(e)}), 500

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
