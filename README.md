# 👗 StyleWithAI – Your AI-Powered Fashion Assistant

StyleWithAI is an intelligent fashion recommendation app that helps users match outfits based on mood, occasion, season, age, and body type — powered by OpenAI and Streamlit.

Upload your clothing item image and get AI-personalized styling tips — available in multiple languages and with text-to-speech output.

---

## 🚀 Features

✅ Upload clothing image (JPG/PNG)  
✅ Select style preferences (Occasion, Season, Mood, Age, Body Type)  
✅ Get smart AI-powered outfit suggestions  
✅ Translate suggestions into 5 languages (English, Roman Urdu, French, German, Portuguese)  
✅ Listen to recommendations using built-in text-to-speech  
✅ Explore fashion tips for Travel & Trends  
✅ “Style Memory” – remembers your uploads during the session  
✅ Mobile-first UI with animated backgrounds and intuitive layout

---

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) – frontend UI  
- [Flask + Render](https://render.com/) – backend API  
- [OpenAI GPT-4 Vision API](https://platform.openai.com/) – outfit suggestions  
- [Deep Translator](https://pypi.org/project/deep-translator/) – translation  
- [gTTS](https://pypi.org/project/gTTS/) – text-to-speech

---

## 🖼️ Live Demo

🔗 [Click to Try the App](https://gosho1992-stylesync-backend-frontend-0zlCqx.streamlit.app)

---

## 💻 How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/stylewithai.git
cd stylewithai

# 2. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # for Windows

# 3. Install requirements
pip install -r requirements.txt

# 4. Run the app
streamlit run frontend.py
