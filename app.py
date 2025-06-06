from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import openai
import stripe
from werkzeug.utils import secure_filename
import traceback
import re

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)  # ✅ Enables cross-origin requests (important for Streamlit frontend)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Make sure this is set in Render

# --- Stripe Checkout Route ---
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        YOUR_FRONTEND_URL = "https://gosho1992-stylesync-backend-frontend-0zlcqx.streamlit.app"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 500,
                    "product_data": {
                        "name": "Premium AI Fashion Analysis"
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{YOUR_FRONTEND_URL}?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=YOUR_FRONTEND_URL,
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Style Detection Logic ---
STYLE_PROFILES = {
    "south_asian": {
        "keywords": ["kurti", "salwar", "lehenga", "sari", "jhumka"],
        "prompt": """Suggest authentic South Asian styling with:
        - Traditional garment names
        - Regional fabric knowledge
        - Cultural occasion guidance
        - Jewelry pairings"""
    },
    "east_asian": {
        "keywords": ["hanbok", "qipao", "kimono", "samfu"],
        "prompt": """Recommend East Asian fashion with:
        - Proper garment terminology
        - Seasonal considerations
        - Modern fusion ideas"""
    },
    "western": {
        "keywords": ["blazer", "jeans", "dress", "sneakers"],
        "prompt": """Suggest contemporary Western looks with:
        - Current runway trends
        - Streetwear influences
        - Brand references"""
    },
    "middle_eastern": {
        "keywords": ["thobe", "abaya", "kandura", "keffiyeh"],
        "prompt": """Style Middle Eastern attire with:
        - Cultural modesty standards
        - Luxury fabric choices
        - Occasion-specific details"""
    },
    "african": {
        "keywords": ["dashiki", "kitenge", "gele", "boubou"],
        "prompt": """Celebrate African fashion by:
        - Incorporating bold prints and textures
        - Reflecting heritage and identity
        - Balancing tradition and trend"""
    },
    "latin_american": {
        "keywords": ["poncho", "guayabera", "pollera", "huipil"],
        "prompt": """Style Latin American outfits with:
        - Vibrant cultural influences
        - Traditional silhouettes
        - Artisan embroidery and flair"""
    },
    "north_american": {
        "keywords": ["flannel", "denim jacket", "cowboy boots", "varsity jacket"],
        "prompt": """Channel North American fashion with:
        - Subcultural streetwear or classic prep
        - Layering for versatility
        - Regional inspirations (NYC, LA, Texas)"""
    }
}


def detect_style(image_b64):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Classify the outfit in the image as ONE of these: south_asian, east_asian, western, middle_eastern, african, latin_american, north_american. Reply with just the keyword (no sentence)."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What fashion culture dominates this outfit?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=100
    )
    return response.choices[0].message.content.strip().lower()


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')

        style = detect_style(image_b64)
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["western"])

        filters = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        prompt = f"""
As a {style.replace('_', ' ').title()} Fashion Concierge, generate a culturally-inspired outfit based on the uploaded item.

{style_profile['prompt']}

Personalize using these traits:
- Body Type: {filters['body_type']} (optimize fit)
- Mood: {filters['mood']}
- Occasion: {filters['occasion']}
- Season: {filters['season']}

Format:
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import openai
import stripe
from werkzeug.utils import secure_filename
import traceback
import re
from dotenv import load_dotenv  # Added for better environment variable handling

# --- Load environment variables first ---
load_dotenv()  # This loads variables from .env file

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY environment variable")

# Initialize clients with error handling
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    stripe.api_key = STRIPE_SECRET_KEY
except Exception as e:
    raise RuntimeError(f"Failed to initialize API clients: {str(e)}")

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Configure upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# --- Health Check Endpoint ---
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "services": {
        "openai": bool(OPENAI_API_KEY),
        "stripe": bool(STRIPE_SECRET_KEY)
    }})

# --- Enhanced Stripe Checkout Route ---
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        YOUR_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://gosho1992-stylesync-backend-frontend-0zlcqx.streamlit.app")
        
        if not YOUR_FRONTEND_URL:
            return jsonify({"error": "Frontend URL not configured"}), 500

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 500,  # $5.00
                    "product_data": {
                        "name": "Premium AI Fashion Analysis",
                        "description": "Unlock advanced outfit analysis and personalized recommendations"
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{YOUR_FRONTEND_URL}?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=YOUR_FRONTEND_URL,
            metadata={
                "service": "fashion_ai",
                "user_ip": request.remote_addr
            }
        )
        return jsonify({"url": checkout_session.url})
    except stripe.error.StripeError as e:
        app.logger.error(f"Stripe error: {str(e)}")
        return jsonify({"error": "Payment processing error"}), 500
    except Exception as e:
        app.logger.error(f"Checkout error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# --- Style Detection Logic ---
STYLE_PROFILES = {
    "south_asian": {
        "keywords": ["kurti", "salwar", "lehenga", "sari", "jhumka"],
        "prompt": """Suggest authentic South Asian styling with:
        - Traditional garment names
        - Regional fabric knowledge
        - Cultural occasion guidance
        - Jewelry pairings"""
    },
    # ... [keep your existing style profiles] ...
}

def detect_style(image_b64):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Classify the outfit in the image as ONE of these: south_asian, east_asian, western, middle_eastern, african, latin_american, north_american. Reply with just the keyword (no sentence)."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What fashion culture dominates this outfit?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=100,
            timeout=10  # Added timeout
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        app.logger.error(f"Style detection failed: {str(e)}")
        return "western"  # Fallback style

# --- Enhanced Upload Endpoint ---
@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Secure filename and save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Read and encode image
        with open(temp_path, "rb") as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Clean up temp file
        os.remove(temp_path)

        # Process image
        style = detect_style(image_b64)
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["western"])

        # Get filters with defaults
        filters = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        prompt = f"""
As a {style.replace('_', ' ').title()} Fashion Concierge, generate a culturally-inspired outfit based on the uploaded item.

{style_profile['prompt']}

Personalize using these traits:
- Body Type: {filters['body_type']} (optimize fit)
- Mood: {filters['mood']}
- Occasion: {filters['occasion']}
- Season: {filters['season']}

Format:

## Signature Look: [Theme Name]
🌟 Vibe: [Mood/Style]
👗 Garment: [Key item + detail]
🧥 Layer: [Adaptation layer + weather]
💎 Accents: [Three accessories with cultural touch]
📏 Fit Tip: [Fit advice based on body type]
⚡ Final Flair: [1-line quote to boost confidence]
"""

        # Generate outfit suggestion
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a globally-minded fashion expert."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=1200,
            timeout=20  # Added timeout
        )

        outfit = response.choices[0].message.content

        return jsonify({
            "status": "success",
            "style": style,
            "fashion_suggestion": outfit,
            "meta": filters
        })

    except openai.APIError as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": "AI service unavailable", "code": "ai_error"}), 503
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Processing failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
