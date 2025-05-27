from flask import Flask, request, jsonify
import os
import base64
import openai
from werkzeug.utils import secure_filename
import traceback
from typing import Dict, Any

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Style Profiles
STYLE_PROFILES = {
    "south_asian": {
        "gender_rules": {
            "Man": "...",
            "Woman": "..."
        },
        "prompt": """Suggest authentic South Asian styling with:
1. Traditional garment names (specify regional variations)
2. Fabric recommendations for {season}
3. Cultural appropriateness for {occasion}
4. Jewelry pairings with historical significance"""
    },
    "western": {
        "gender_rules": {},
        "prompt": """Suggest a modern Western outfit suitable for {season} and {occasion}.
- Mix basics with statement pieces
- Prioritize functionality + trend
- Reflect mood: {mood}"""
    }
    # Add other profiles as needed
}

GENDER_GUIDELINES = {
    "Man": "...",
    "Woman": "...",
    "Non-binary": "..."
}

# ✅ Enhanced Detection with Exception Handling
def detect_style(image_b64: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """Classify the dominant cultural fashion style of the uploaded image into:
- south_asian
- east_asian
- western
- middle_eastern
- african
- latin_american
- north_american
Respond with one keyword only."""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this clothing style:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"❌ Style detection failed: {str(e)}")
        return "western"  # fallback

# ✅ Fix: Accept style as an argument
def generate_outfit_prompt(filters: Dict[str, Any], style: str, style_profile: Dict[str, Any]) -> str:
    gender = filters["gender"]
    return f"""As a {style.replace('_', ' ').title()} Fashion Director, create a {filters['occasion']} outfit for a {filters['age']} {gender} with {filters['body_type']} build. The mood should be {filters['mood']} and suitable for {filters['season']}.

**CULTURAL GUIDELINES**
{style_profile['prompt'].format(**filters)}

**GENDER-SPECIFIC RULES**
{GENDER_GUIDELINES.get(gender, GENDER_GUIDELINES['Non-binary'])}

**OUTPUT REQUIREMENTS**
## [Theme Name] 
🌍 Cultural Roots: [Heritage context]
👔 Core Ensemble: [Main + Layer]
✨ Style Hack: [Unexpected twist]
📏 Fit Mastery: [Advice for {filters['body_type']} body]
🧩 Accents: 3 accessories tailored for {gender}
"""

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # ✅ Extract uploaded file and form data
        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')

        filters = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        style = detect_style(image_b64)
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["western"])

        # ✅ Guardrail against accessory mismatches
        def is_gender_appropriate(suggestion: str, gender: str) -> bool:
            gender = gender.lower()
            warning_signs = {
                "man": ["headband", "fringe bag", "anklet", "peplum"],
                "woman": ["boxy cut", "oversized", "menswear watch"]
            }
            return not any(
                term in suggestion.lower() 
                for term in warning_signs.get(gender, [])
            )

        # ✅ Generate Fashion Suggestion (up to 3 tries)
        for _ in range(3):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a cultural fashion curator."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": generate_outfit_prompt(filters, style, style_profile)},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            suggestion = response.choices[0].message.content
            if is_gender_appropriate(suggestion, filters["gender"]):
                break
        else:
            suggestion += "\n\n⚠️ Some accessory suggestions may not fully align with gender."

        return jsonify({
            "status": "success",
            "style": style,
            "fashion_suggestion": suggestion,
            "meta": filters
        })

    except Exception as e:
        print(f"❌ SERVER ERROR: {str(e)}")
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
