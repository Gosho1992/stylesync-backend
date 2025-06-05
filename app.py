from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
import traceback
import re  # Added for potential future prompt parsing
import stripe

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



# Load Stripe secret key from env
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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
            success_url=YOUR_FRONTEND_URL + "?payment=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_FRONTEND_URL,
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Global Style Matrix
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
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
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

        # Detect fashion style
        style = detect_style(image_b64)
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["western"])

        # Filters from frontend
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
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=1200
        )

        outfit = response.choices[0].message.content
        
        # Generate image prompt for Leonardo AI
        image_prompt = (
            f"A {filters['gender'].lower()} wearing {style.replace('_', ' ')} fashion, "
            f"{filters['mood']} mood, {filters['occasion']} occasion. "
            f"Outfit details: {outfit[:300]}. "
            f"Full body shot, photorealistic, high fashion photography style, "
            f"perfect lighting, studio background."
        )

        return jsonify({
            "status": "success",
            "style": style,
            "fashion_suggestion": outfit,
            "image_prompt": image_prompt,  # New field for Leonardo AI
            "meta": filters
        })

    except Exception as e:
        print("❌ ERROR TRACEBACK:")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))