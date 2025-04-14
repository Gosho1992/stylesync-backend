from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Helper: Encode image to base64
def encode_image(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with open(filepath, "rb") as img:
        encoded = base64.b64encode(img.read()).decode("utf-8")
    
    os.remove(filepath)
    return encoded

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ready", "model": "gpt-4o"})

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({"error": "Unsupported file type"}), 400

    # Get form filters
    filters = {
        "occasion": request.form.get("occasion", "Casual"),
        "season": request.form.get("season", "Any"),
        "gender": request.form.get("gender", "Woman"),
        "body_type": request.form.get("body_type", "Average"),
        "age": request.form.get("age", "20s"),
        "mood": request.form.get("mood", "Confident")
    }

    # Convert image
    try:
        image_b64 = encode_image(file)
    except Exception as e:
        return jsonify({"error": "Image processing failed", "details": str(e)}), 500

    # Construct prompt
    prompt = f"""
🎨 As Vogue's Senior AI Stylist, create ONE signature look for:
- Gender: {filters['gender']}
- Age Group: {filters['age']}
- Body Type: {filters['body_type']}
- Occasion: {filters['occasion']}
- Season: {filters['season']}
- Mood: {filters['mood']}

**STRUCTURE THE RESPONSE AS MARKDOWN** like this:

## 👗 Signature Look: [Theme Name]

✨ **Vibe**: [2-word mood theme]  
👕 **Top**: [Item] + [Detail]  
👖 **Bottom**: [Item] + [Detail]  
👟 **Shoes**: [Type] + [Benefit]  
🧥 **Layers**: [Optional outerwear] + [Weather Note]  
💎 **Accents**: 1) [Item] 2) [Item] 3) [Item]  
📏 **Fit Hack**: [Tip for {filters['body_type']}]  
🌈 **Mood Tie-in**: How this outfit boosts {filters['mood']}  
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional fashion stylist who always provides one clear, creative, and formatted look."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                    ]
                }
            ],
            temperature=0.8,
            max_tokens=1000
        )

        suggestion = response.choices[0].message.content.strip()
        return jsonify({
            "status": "success",
            "fashion_suggestion": suggestion,
            "meta": filters
        })

    except Exception as e:
        return jsonify({"error": "OpenAI API failed", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
