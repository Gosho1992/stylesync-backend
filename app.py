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

    # Save uploaded image
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Failed to process image"}), 500

    # Send to OpenAI
    try:
        
prompt = (
    f"You are a high-end fashion stylist. A user has uploaded a clothing item. "
    f"Ignore the person and focus only on styling based on that item. "
    f"Using these filters:\n"
    f"- Occasion: {occasion}\n"
    f"- Season: {season}\n"
    f"- Age Group: {age_group}\n"
    f"- Mood: {mood}\n"
    f"- Region-based fashion (e.g. trench coats in Europe, shalwar kameez in Pakistan)\n\n"

    f"Return a stylish outfit suggestion using this structure in markdown format:\n\n"

    f"**👋 Greeting:**\n"
    f"A short friendly message to set the tone (1–2 lines).\n\n"

    f"**👕 Top (Central Piece):**\n"
    f"A fashionable shirt/top that matches the item + mood.\n\n"

    f"**👖 Bottoms:**\n"
    f"Suggested pants, skirts, or jeans.\n\n"

    f"**👟 Shoes:**\n"
    f"Footwear based on the season & vibe.\n\n"

    f"**🧥 Outerwear:**\n"
    f"Layered jackets or coats depending on weather.\n\n"

    f"**💍 Accessories:**\n"
    f"Suggestions like watch, bag, scarf, sunglasses.\n\n"

    f"**💬 Final Words:**\n"
    f"End with 1–2 lines of friendly, encouraging fashion advice that fits the user's mood.\n\n"

    f"Write in clear, spaced **markdown format** using bullet points where needed. Avoid using '###', just use headings like '**Section Title:**'. "
)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fashion expert. Give stylish and practical fashion suggestions."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=300
        )

        fashion_advice = response.choices[0].message.content

        return jsonify({
            "message": "Image uploaded successfully",
            "filename": filename,
            "fashion_suggestion": fashion_advice
        })

    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return jsonify({"error": "Failed to get response from OpenAI"}), 500

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
