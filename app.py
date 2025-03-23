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

# Route for uploading images and getting fashion suggestions
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

    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Convert image to Base64
    base64_image = encode_image(filepath)
    if not base64_image:
        return jsonify({"error": "Failed to process image"}), 500

    # Send to OpenAI
    try:
        prompt = (
            f"Analyze the clothing item in the image and suggest a matching outfit for a "
            f"{occasion.lower()} occasion in {season.lower()} season."
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


    # Send Image to OpenAI for fashion analysis
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fashion expert. Analyze the clothing in the image and suggest a matching outfit."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analyze this clothing item and suggest a matching outfit."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=300
        )

        # Extract AI-generated fashion advice
        fashion_advice = response.choices[0].message.content

        return jsonify({
            "message": "Image uploaded successfully",
            "filename": filename,
            "fashion_suggestion": fashion_advice
        })

    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return jsonify({"error": "Failed to get response from OpenAI"}), 500

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
