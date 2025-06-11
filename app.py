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
from datetime import datetime

# --- Configuration ---
load_dotenv()

# Environment variables validation
REQUIRED_ENV_VARS = {
    'OPENAI_API_KEY': 'OpenAI API key',
    'STRIPE_SECRET_KEY': 'Stripe secret key',
    'STRIPE_WEBHOOK_SECRET': 'Stripe webhook secret',
    'GOOGLE_SHEET_API_URL': 'Google Sheets API URL'
}

missing_vars = [name for name, desc in REQUIRED_ENV_VARS.items() if not os.getenv(name)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize services
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
app = Flask(__name__)
CORS(app)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# --- Constants ---
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config.update({
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    'MAX_CONTENT_LENGTH': MAX_FILE_SIZE
})

# --- Helper Functions ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_email(email):
    """Basic email validation"""
    return '@' in email and '.' in email.split('@')[-1]

# --- API Endpoints ---
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'stripe': bool(os.getenv('STRIPE_SECRET_KEY')),
            'google_sheets': bool(os.getenv('GOOGLE_SHEET_API_URL'))
        }
    }), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle image uploads for style detection"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Secure filename and save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Process image
        with open(temp_path, 'rb') as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Clean up
        os.remove(temp_path)
        
        # Detect style (with timeout)
        style = detect_style(image_b64)
        
        return jsonify({
            'status': 'success',
            'style': style,
            'processed_at': datetime.utcnow().isoformat()
        }), 200
        
    except openai.APIError as e:
        logger.error(f'OpenAI API error: {str(e)}')
        return jsonify({
            'error': 'AI service unavailable',
            'code': 'ai_error'
        }), 503
    except Exception as e:
        logger.error(f'Upload error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': 'Processing failed',
            'details': str(e)
        }), 500

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session"""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    email = data['email'].strip()
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 500,  # $5.00
                    'product_data': {
                        'name': 'StyleWithAI Premium',
                        'description': 'AI-powered outfit analysis'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=email,
            success_url=os.getenv('SUCCESS_URL', 'https://yourdomain.com/success'),
            cancel_url=os.getenv('CANCEL_URL', 'https://yourdomain.com/cancel'),
            metadata={
                'service': 'stylewithai',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f'Created checkout session for {email}')
        return jsonify({
            'sessionId': checkout_session.id,
            'url': checkout_session.url
        }), 200
        
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error: {str(e)}')
        return jsonify({
            'error': 'Payment processing error',
            'details': str(e.user_message if hasattr(e, 'user_message') else str(e))
        }), 500
    except Exception as e:
        logger.error(f'Checkout error: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        logger.error('Missing Stripe signature header')
        return jsonify({'error': 'Missing signature header'}), 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        logger.error(f'Invalid payload: {str(e)}')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Signature verification failed: {str(e)}')
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle specific event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        
        if not customer_email:
            logger.error('No email in completed session')
            return jsonify({'error': 'No customer email'}), 400
        
        try:
            # Update Google Sheet
            response = requests.post(
                os.getenv('GOOGLE_SHEET_API_URL'),
                json={
                    'email': customer_email,
                    'status': 'paid',
                    'payment_id': session.get('id'),
                    'amount': session.get('amount_total', 500) / 100  # Convert cents to dollars
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f'Updated payment status for {customer_email}')
            else:
                logger.error(f'Google Sheets update failed: {response.status_code}')
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Google Sheets API error: {str(e)}')
    
    return jsonify({'status': 'success'}), 200

# --- Service Functions ---
import time

def detect_style(image_b64, max_retries=3):
    """Use OpenAI to detect clothing style with retries"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {
                        'role': 'system',
                        'content': 'Classify the outfit style from the image. Respond with ONLY one of: south_asian, east_asian, western, middle_eastern, african, latin_american, north_american'
                    },
                    {
                        'role': 'user',
                        'content': [
                            { 'type': 'text', 'text': 'Classify this outfit:' },
                            { 'type': 'image_url', 'image_url': { 'url': f'data:image/jpeg;base64,{image_b64}' } }
                        ]
                    }
                ],
                max_tokens=50,
                timeout=15
            )

            style = response.choices[0].message.content.strip().lower()
            logger.info(f'Detected style: {style}')
            return style

        except openai.APIError as e:
            logger.warning(f'OpenAI APIError on attempt {attempt}/{max_retries}: {str(e)}')

            # If not last attempt, wait and retry
            if attempt < max_retries:
                wait_time = 2 * attempt  # exponential backoff
                logger.info(f'Waiting {wait_time} seconds before retrying...')
                time.sleep(wait_time)
            else:
                # Last attempt failed — raise to caller (will trigger your 503 logic)
                logger.error('All OpenAI API attempts failed.')
                raise e

        except Exception as e:
            # For other unexpected errors
            logger.error(f'Unexpected error in detect_style: {str(e)}\n{traceback.format_exc()}')
            raise e


@app.route('/check-premium', methods=['GET'])
def check_premium():
    """Proxy GET request to Google Sheet API to check premium status"""
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Missing email parameter'}), 400
    
    try:
        response = requests.get(
            os.getenv('GOOGLE_SHEET_API_URL'),
            params={'email': email},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f'Checked premium status for {email}')
            return jsonify(response.json()), 200
        else:
            logger.error(f'Failed to check premium status: {response.status_code}')
            return jsonify({'error': 'Failed to check premium status'}), response.status_code
        
    except requests.exceptions.RequestException as e:
        logger.error(f'Error checking premium status: {str(e)}')
        return jsonify({'error': str(e)}), 500


# --- Main ---
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)