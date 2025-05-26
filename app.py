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

# Enhanced Style Matrix with Gender Nuances
STYLE_PROFILES = {
    "south_asian": {
        "gender_rules": {
            "Man": """- Focus on: Bandhgalas, Jodhpuris, structured kurtas
- Avoid: Delicate embroidery, flowing silhouettes
- Key accessories: Mojris, brooches, pocket squares""",
            "Woman": """- Embrace: Anarkalis, lehengas, dupatta draping
- Key accessories: Jhumkas, maang tikkas, potli bags"""
        },
        "prompt": """Suggest authentic South Asian styling with:
1. Traditional garment names (specify regional variations)
2. Fabric recommendations for {season}
3. Cultural appropriateness for {occasion}
4. Jewelry pairings with historical significance"""
    },
    # ... [other cultural profiles with similar gender rules] ...
}

# Gender-Specific Fashion Rules
GENDER_GUIDELINES = {
    "Man": """MALE FASHION RULES:
1. Silhouettes: Structured, angular cuts
2. Accessories: Minimal (max 3 pieces), functional
3. Colors: Earth tones or bold solids preferred
4. Proportions: Should emphasize shoulder-to-waist ratio
5. Avoid: Sheer fabrics, excessive embellishment""",
    
    "Woman": """FEMALE FASHION RULES:
1. Silhouettes: Can range from fitted to flowing
2. Accessories: Layering encouraged
3. Colors: Full spectrum acceptable
4. Proportions: Waist definition recommended
5. Avoid: Nothing strictly prohibited""",
    
    "Non-binary": """GENDER-NEUTRAL RULES:
1. Mix masculine and feminine elements intentionally
2. Focus on personal expression over norms
3. Androgynous tailoring recommended"""
}

def detect_style(image_b64: str) -> str:
    """Enhanced style detection with cultural sensitivity"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Analyze the outfit's cultural roots. Classify as ONE of:
- south_asian (for Subcontinent styles)
- east_asian (traditional Chinese/Japanese/Korean)
- western (Euro/American)
- middle_eastern (Gulf/Arabic)
- african (traditional prints/textiles)
- latin_american (vibrant folkloric)
- north_american (casual/streetwear)
Return ONLY the keyword."""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify the dominant cultural style:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip().lower()

def generate_outfit_prompt(filters: Dict[str, Any], style_profile: Dict[str, Any]) -> str:
    """Constructs a culturally-grounded, gender-sensitive prompt"""
    gender = filters["gender"]
    
    return f"""As a {style.replace('_', ' ').title()} Fashion Director, create a {filters['occasion']} outfit for a {filters['age']} {gender} with {filters['body_type']} build. The mood should be {filters['mood']} and suitable for {filters['season']}.

**CULTURAL GUIDELINES**
{style_profile['prompt'].format(**filters)}

**GENDER-SPECIFIC RULES**
{GENDER_GUIDELINES.get(gender, GENDER_GUIDELINES['Non-binary'])}

**OUTPUT REQUIREMENTS**
1. **Theme**: Create a compelling style narrative (2-3 words)
2. **Garments**: 
   - Main piece (describe cut/fabric)
   - Complementary layers
3. **Accents**: 3 culturally-relevant accessories
4. **Fit Intelligence**: Tailoring advice for {filters['body_type']}
5. **Cultural Note**: Explain one traditional element
6. **Modern Twist**: Suggest one contemporary adaptation

Format in markdown with emoji headers:
## [Theme Name] 
🌍 Cultural Roots: [Heritage context]
👔 Core Ensemble: [Detailed description]
✨ Style Hack: [Unique pairing idea]
📏 Fit Mastery: [Body-specific advice]"""

@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')
        style = detect_style(image_b64)
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["western"])

        # Validate gender-specific items
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

        filters = {
            "occasion": request.form.get("occasion", "Casual"),
            "season": request.form.get("season", "Any"),
            "gender": request.form.get("gender", "Woman"),
            "body_type": request.form.get("body_type", "Average"),
            "age": request.form.get("age", "20s"),
            "mood": request.form.get("mood", "Confident")
        }

        # Generate with validation loop
        for _ in range(3):  # Max 3 attempts
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a cultural fashion curator."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": generate_outfit_prompt(filters, style_profile)},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
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
            suggestion += "\n\n⚠️ Note: Some recommendations may need gender-specific adjustments"

        return jsonify({
            "status": "success",
            "style": style,
            "fashion_suggestion": suggestion,
            "meta": filters
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))