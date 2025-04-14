from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
from time import sleep

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("API key missing")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def process_image(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    with open(filepath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    os.remove(filepath)
    return encoded_image

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['file']
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        # Process image and form data
        base64_image = process_image(file)
        styling_data = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        # Enhanced prompt with fallback instructions
        prompt = f"""As Vogue's lead stylist, create 2 looks for:
- {styling_data['gender']} aged {styling_data['age']}
- Body type: {styling_data['body_type']}
- Mood: {styling_data['mood']}
- Season: {styling_data['season']}
- Occasion: {styling_data['occasion']}

Format strictly as:

LOOK 1: [Theme Name]
✨ Vibe: [2-3 words]
👕 Top: [Item] + [Detail]
👖 Bottom: [Item] + [Detail]
👟 Shoes: [Type] + [Benefit]
🧥 Layers: [Item] + [Weather Note]
💎 Accents: 1) [Item] 2) [Item] 3) [Item]
📏 Fit Hack: {styling_data['body_type']}-specific tip

LOOK 2: [Different Theme]
[Same structure]

⚡ Pro Tip: [Cross-outfit advice]"""

        # Retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a precise fashion AI. Never say you can't suggest outfits."
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
                    temperature=0.7,
                    max_tokens=1200
                )
                
                suggestion = response.choices[0].message.content
                if "LOOK 1:" in suggestion and "LOOK 2:" in suggestion:
                    return jsonify({
                        "status": "success",
                        "suggestion": suggestion,
                        "meta": styling_data
                    })
                
                sleep(1)  # Wait before retry

            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                sleep(2)
                continue

        return jsonify({"error": "Incomplete suggestions"}), 500

    except Exception as e:
        return jsonify({
            "error": "Styling service unavailable",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))