from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ready", "version": "2.0"})

@app.route("/upload", methods=["POST"])
def upload_image():
    # Validate file
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Get all styling parameters
    styling_params = {
        "occasion": request.form.get("occasion", "Casual"),
        "season": request.form.get("season", "Any"),
        "gender": request.form.get("gender", "Woman"),
        "body_type": request.form.get("body_type", "Average"),
        "age": request.form.get("age", "20s"),
        "mood": request.form.get("mood", "Confident"),
        "format_instructions": request.form.get("format_instructions", "")
    }

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Process image
    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Image processing failed"}), 500

    # Generate fashion prompt
    prompt = f"""
As Creative Director of {styling_params['gender']}'s fashion at Vogue, create 2 complete looks based on:
- 👗 Body Type: {styling_params['body_type']}-optimized silhouettes
- 🎯 Occasion: {styling_params['occasion']}-appropriate styling
- 🌦️ Season: {styling_params['season']}-specific fabrics
- 😌 Mood: {styling_params['mood']}-enhancing colors
- 👑 Age: {styling_params['age']}-relevant trends

**Structure each look with:**
1. ✨ THEME: 2-word aesthetic
2. 🧥 OUTFIT: 3-5 pieces with technical details
3. 📏 FIT HACK: {styling_params['body_type']}-specific trick
4. 💎 ACCENTS: 3 curated accessories
5. ⚡ IMPACT: How this elevates the wearer

Format exactly as:
## LOOK 1: [Theme]
- ✨ Vibe: [description]
- 👕 Top: [item] + [fabric] + [styling tip]
- 👖 Bottom: [item] + [fit note] 
- 👟 Shoes: [type] + [functional benefit]
- 📏 Fit Hack: [specific to {styling_params['body_type']}]
- 💎 Accents: 1) [item] 2) [item] 3) [item]
- ⚡ Why: [confidence/mood boost]

## LOOK 2: [Different Theme]
[Same structure]

💡 Universal Tip: Cross-seasonal styling advice
"""

    try:
        # Call OpenAI with image and enhanced prompt
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior fashion stylist specializing in personalized looks."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        # Clean up
        os.remove(filepath)

        return jsonify({
            "status": "success",
            "fashion_suggestion": response.choices[0].message.content,
            "meta": styling_params
        })

    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({"error": "Fashion engine overloaded", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)