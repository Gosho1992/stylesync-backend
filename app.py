from flask import Flask, request, jsonify
import os
import openai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("ERROR: OpenAI API key is missing. Set OPENAI_API_KEY in the environment.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Flask app setup
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ready", "version": "2.2"})

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Filename missing"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file format"}), 400

    # Extract filters
    styling = {
        "occasion": request.form.get("occasion", "Casual"),
        "season": request.form.get("season", "Any"),
        "gender": request.form.get("gender", "Woman"),
        "body_type": request.form.get("body_type", "Average"),
        "age": request.form.get("age", "20s"),
        "mood": request.form.get("mood", "Confident"),
        "format_instructions": request.form.get("format_instructions", "")
    }

    # Save uploaded image (not used in prompt for now)
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Build GPT prompt
    prompt = f"""
As Creative Director of {styling['gender']}'s fashion at Vogue, create 2 complete looks based on:
- 👗 Body Type: {styling['body_type']}
- 🎯 Occasion: {styling['occasion']}
- 🌦️ Season: {styling['season']}
- 😌 Mood: {styling['mood']}
- 👑 Age Group: {styling['age']}

{styling['format_instructions'] or "Use emojis, clear outfit labels, and short stylish descriptions. Focus on mood + fit + vibe."}
"""

    try:
        # GPT-4 Text-only Call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior fashion stylist who gives personalized outfit recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        suggestion = response.choices[0].message.content.strip()

        # Clean up saved image
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            "status": "success",
            "fashion_suggestion": suggestion,
            "meta": styling
        })

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "OpenAI API failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
