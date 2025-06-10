from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import openai
import stripe
import requests
import traceback
import logging
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# --- Configuration ---
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRIPE_API_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
GOOGLE_SHEET_API_URL = "https://script.google.com/macros/s/AKfyc66NuoQyt8cI91wtVo6_9Fh2gyVSZJZsqk7GeL7n01K4qywyI2Q71_0mMLOKFRhlK7/exec"

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")
if not STRIPE_API_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY environment variable")
if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("Missing STRIPE_WEBHOOK_SECRET environment variable")

# Initialize Stripe client
stripe.api_key = STRIPE_API_KEY

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
            "stripe_key_present": bool(STRIPE_API_KEY),
            "webhook_secret_present": bool(STRIPE_WEBHOOK_SECRET)
        }
    })

# --- Style Detection ---
def detect_style(image_b64):
    app.logger.info("Detecting style...")
    try:
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
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        with open(temp_path, "rb") as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode('utf-8')

        os.remove(temp_path)

        style = detect_style(image_b64)

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

# --- Stripe Webhook Endpoint ---
@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    app.logger.info("Stripe webhook called")
    payload = request.data
    sig_header = request.headers.get("stripe-signature", None)

    if not sig_header:
        app.logger.error("Missing Stripe signature header")
        return jsonify(success=False), 400

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        app.logger.error(f"Webhook signature verification failed: {str(e)}")
        return jsonify(success=False), 400
    except Exception as e:
        app.logger.error(f"Webhook error: {str(e)}")
        return jsonify(success=False), 400

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")

        app.logger.info(f"Payment completed for email: {customer_email}")

        # Call Google Sheets API to mark as paid
        try:
            params = {
                "email": customer_email,
                "status": "paid"
            }
            response = requests.get(GOOGLE_SHEET_API_URL, params=params, timeout=10)
            if response.status_code == 200:
                app.logger.info(f"Marked {customer_email} as paid in Google Sheet")
            else:
                app.logger.error(f"Failed to mark paid in Google Sheet: {response.status_code}, {response.text}")
        except Exception as e:
            app.logger.error(f"Error calling Google Sheet API: {str(e)}")

    return jsonify(success=True), 200

# --- Run App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
