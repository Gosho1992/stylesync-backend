from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("ERROR: OpenAI API key is missing. Set OPENAI_API_KEY in the environment.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Validate file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Convert image to base64 string
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ready", "version": "2.1"})

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No filename found"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    # Extract style fields
    styling = {
        "occasion": request.form.get("occasion", "Casual"),
        "season": request.form.get("season", "Any"),
        "gender": request.form.get("gender", "Woman"),
        "body_type": request.form.get("body_type", "Average"),
        "age": request.form.get("age", "20s"),
        "mood": request.form.get("mood", "Confident"),
        "format_instructions": request.form.get("format_instructions", "")
    }

    # Save image locally
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Encode for OpenAI
    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Failed to process image"}), 500

    # Construct prompt
    prompt = f"""
As Creative Director of {styling['gender']}'s fashion at Vogue, create 2 complete looks based on:
- 👗 Body Type: {styling['body_type']}-optimized silhouettes
- 🎯 Occasion: {styling['occasion']}-appropriate styling
- 🌦️ Season: {styling['season']}-specific fabrics
- 😌 Mood: {styling['mood']}-enhancing colors
- 👑 Age: {styling['age']}-relevant trends

{styling['format_instructions'] or "Use a stylistic, clear structure with emoji headings and short paragraphs."}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior fashion stylist specializing in personalized looks."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                    ]
                }
            ],
            max_tokens=1000
        )

        content = response.choices[0].message.content.strip()

        os.remove(filepath)

        return jsonify({
            "status": "success",
            "fashion_suggestion": content,
            "meta": styling
        })

    except Exception as e:
        print("❌ Error:", str(e))
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "OpenAI API failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
