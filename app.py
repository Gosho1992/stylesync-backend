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
    f"Aap ek high-end fashion stylist hain jo user ko personally style kar raha hai. "
    f"Uploaded item ko central piece samjhein, lekin baqi complete outfit (shoes, pants, jacket, accessories) ka suggestion dein. "
    f"User ne occasion select kiya hai: '{occasion.lower()}', season: '{season.lower()}', age group: '{age_group.lower()}', mood: '{mood.lower()}'. "
    f"In filters ko samajh kar ek stylish theme tay karein (e.g. playful, romantic, elegant). "
    f"Har item (top, bottom, shoes, accessories, outerwear) ke liye ek trendy aur culture-aware recommendation dein – jaise agar user Pakistan mein ho toh shalwar kameez ya sandals ka zikar ho sakta hai. "
    f"Style ko real stylist ki tarah samjhayen, jaise aap user se baat kar rahe ho. "
    f"Jaise: 'Since you're feeling {mood.lower()} today and it's {season.lower()}, I’d pair that with…' "
    f"Suggestions ko bullet points mein dein – aur last mein ek chhoti si summary bhi dein ke overall look kaisa lagega."
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
