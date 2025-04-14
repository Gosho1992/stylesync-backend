
from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
from time import sleep

# Load API key from environment
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
        base64_image = process_image(file)
        styling = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        # Streamlined prompt for ONE refined look with clean formatting
        prompt = f"""
You are a world-class AI stylist. Generate one refined fashion look based on the client's preferences.

👤 Client Profile:
- Gender: {styling['gender']}
- Age: {styling['age']}
- Body Type: {styling['body_type']}
- Occasion: {styling['occasion']}
- Season: {styling['season']}
- Mood: {styling['mood']}

🎨 Return result in this exact format with emoji headers and short, styled paragraphs:

🖤 **Signature Look**: [1-line title, e.g., "Boho Bloom" or "Parisian Edge"]

🔍 **Style Breakdown**:
- 👗 **Top**: [Description with fabric, cut, and styling tip]
- 👖 **Bottom**: [Fit + occasion-relevance]
- 👟 **Shoes**: [Comfort + seasonal fit]
- 🧥 **Layers**: [Outerwear, culture/style nod]
- 💎 **Accessories**: [3 thoughtful items for utility or flair]
- 📏 **Fit Hack**: [Body-type specific enhancement]

💡 **Stylist Affirmation**: [One motivational sentence in quotes]
"""

        retries = 3
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a highly intelligent fashion assistant. "
                                "Always return a single, perfectly formatted suggestion. Be visual and stylish."
                            )
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
                    max_tokens=1100
                )

                suggestion = response.choices[0].message.content.strip()

                if suggestion and len(suggestion) > 80:
                    return jsonify({
                        "status": "success",
                        "suggestion": suggestion,
                        "meta": styling
                    })

            except Exception as e:
                if attempt == retries - 1:
                    return jsonify({"error": "OpenAI API failed", "details": str(e)}), 500
                sleep(2)

        return jsonify({"error": "Incomplete suggestions"}), 500

    except Exception as e:
        return jsonify({
            "error": "Styling service unavailable",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
