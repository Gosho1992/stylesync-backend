from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename

# Configuration
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
    return jsonify({"status": "ready", "model": "gpt-4o"})

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

    # Get styling parameters
    styling_params = {
        "occasion": request.form.get("occasion", "Casual"),
        "season": request.form.get("season", "Any"),
        "gender": request.form.get("gender", "Woman"),
        "body_type": request.form.get("body_type", "Average"),
        "age": request.form.get("age", "20s"),
        "mood": request.form.get("mood", "Confident")
    }

    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Image processing failed"}), 500

    # Enhanced prompt with strict formatting
    prompt = f"""
As {styling_params['gender']}'s Creative Director at Vogue, create 2 looks focusing on:
- Body Type: {styling_params['body_type']}-specific fits
- Mood: {styling_params['mood']}-enhancing colors
- Season: {styling_params['season']}-appropriate fabrics

**Required Format (NO deviations):**

LOOK 1: [2-Word Theme Name]
✨ Vibe: [mood descriptor]
👕 Top: [item] + [fabric] + [styling tip]
👖 Bottom: [item] + [fit detail] 
👟 Shoes: [type] + [functional benefit]
🧥 Layers: [item] + [weather adaptation]
💎 Accents: 1) [item] 2) [item] 3) [item]
📏 Fit Hack: {styling_params['body_type']}-specific trick

LOOK 2: [Different Theme]
[Same structure as above]

⚡ Style Tip: Cross-item styling advice
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Maintained as requested
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise fashion stylist. Follow formatting exactly."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,  # Controls creativity vs precision
            max_tokens=1200
        )

        # Clean up
        os.remove(filepath)

        return jsonify({
            "status": "success",
            "suggestion": response.choices[0].message.content,
            "meta": styling_params
        })

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)