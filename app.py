from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
from time import sleep

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Set your OPENAI_API_KEY in environment.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- Utils ----------
def process_image(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    with open(filepath, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
    
    os.remove(filepath)
    return encoded

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "StyleSync AI is live", "version": "3.0"})

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

# ---------- Main Upload Endpoint ----------
@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({"error": "Invalid image type"}), 400

    try:
        base64_image = process_image(file)
        filters = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        prompt = f"""
You are a senior fashion stylist. Generate a personalized outfit suggestion based on:
- Occasion: {filters['occasion']}
- Season: {filters['season']}
- Gender: {filters['gender']}
- Age Group: {filters['age']}
- Mood: {filters['mood']}
- Body Type: {filters['body_type']}

Respond in a clean Markdown format like this:

## Signature Look: [Theme Name]
- ✨ **Vibe**: [2-word style tone]
- 👕 **Top**: [item] + [fabric/cut] + [tip]
- 👖 **Bottom**: [item] + [fit] + [reason]
- 👟 **Shoes**: [type] + [comfort] + [season match]
- 🧥 **Layer**: [piece] + [weather fit] + [cultural style]
- 💎 **Accents**: 1) [item] 2) [item] 3) [item]
- 📏 **Fit Hack**: [body-type focused tip]
- ⚡ **Final Flair**: [closing line with energy]
"""

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a creative yet practical fashion assistant. Always return useful suggestions."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "auto"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1200,
                    temperature=0.7,
                    timeout=20  # timeout for OpenAI response
                )

                suggestion = response.choices[0].message.content.strip()
                if suggestion:
                    return jsonify({
                        "status": "success",
                        "fashion_suggestion": suggestion,
                        "meta": filters
                    })

            except Exception as e:
                print(f"Retry {attempt + 1} failed: {e}")
                sleep(2)

        return jsonify({
            "error": "Fashion engine is waking up or under load. Try again in a moment."
        }), 503

    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({
            "error": "Unexpected server error",
            "details": str(e)
        }), 500

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
