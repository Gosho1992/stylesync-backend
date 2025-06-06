from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import openai
import stripe
from werkzeug.utils import secure_filename
import traceback
import logging
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY environment variable")

# Initialize Stripe client
stripe.api_key = STRIPE_SECRET_KEY

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Enable logging
logging.basicConfig(level=logging.DEBUG)
app.logger.info("Flask app started successfully")

# Upload config
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# --- Health Check Endpoint ---
@app.route("/health", methods=["GET"])
def health_check():
    app.logger.info("Health check called")
    return jsonify({
        "status": "healthy",
        "services": {
            "openai_key_present": bool(OPENAI_API_KEY),
            "stripe_key_present": bool(STRIPE_SECRET_KEY)
        }
    })

# --- Stripe Checkout ---
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        YOUR_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://gosho1992-stylesync-backend-frontend-0zlcqx.streamlit.app")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 500,
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
        app.logger.info("Stripe checkout session created successfully")
        return jsonify({"url": checkout_session.url})
    except stripe.error.StripeError as e:
        app.logger.error(f"Stripe error: {str(e)}")
        return jsonify({"error": "Payment processing error"}), 500
    except Exception as e:
        app.logger.error(f"Checkout error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# --- Style Detection ---
def detect_style(image_b64):
    app.logger.info("Detecting style...")
    try:
        # Initialize OpenAI client INSIDE the function (safe)
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
            timeout=10
        )
        style = response.choices[0].message.content.strip().lower()
        app.logger.info(f"Detected style: {style}")
        return style
    except Exception as e:
        app.logger.error(f"Style detection failed: {str(e)}")
        return "western"  # fallback

# --- Upload Endpoint ---
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

        # Example response:
        return jsonify({
            "status": "success",
            "style": style
        })

    except openai.APIError as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": "AI service unavailable", "code": "ai_error"}), 503
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Processing failed", "details": str(e)}), 500

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
