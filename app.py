from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename

# Load your API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("ERROR: OpenAI API key is missing.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ StyleSync backend running", "version": "2.0"})

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Get styling inputs
    occasion = request.form.get("occasion", "Casual")
    season = request.form.get("season", "Any")
    gender = request.form.get("gender", "Woman")
    body_type = request.form.get("body_type", "Average")
    age = request.form.get("age", "20s")
    mood = request.form.get("mood", "Confident")
    format_instructions = request.form.get("format_instructions", "")

    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Image processing failed"}), 500

    prompt = f"""
As Creative Director of {gender}'s fashion at Vogue, design 2 stunning outfits using:
- 🎯 Occasion: {occasion}
- 🌦️ Season: {season}
- 🧍 Body Type: {body_type}
- 🎂 Age: {age}
- 😌 Mood: {mood}

{format_instructions or "Use markdown headings, short emojis, and tips specific to body type and mood."}
"""

    try:
        # GPT-4o supports image input
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You're a fashion stylist helping clients choose personalized looks."},
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

        suggestion = response.choices[0].message.content

        os.remove(filepath)

        return jsonify({
            "status": "success",
            "fashion_suggestion": suggestion,
            "meta": {
                "occasion": occasion,
                "season": season,
                "gender": gender,
                "body_type": body_type,
                "age": age,
                "mood": mood
            }
        })

    except Exception as e:
        print("❌ Error:", str(e))
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "OpenAI API error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
