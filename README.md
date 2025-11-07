# ✈️ NomadSquad — Your AI Travel Planner

> **Books in one hand, backpack in the other.**  
> Smart. Funny. Personalized. NomadSquad is your AI-powered travel companion that crafts tailor-made adventures for every traveler.  

🌍 **Live Demo:** [https://nomadsquad.streamlit.app/](https://nomadsquad.streamlit.app/) 🚀  

---

## 🧠 Overview

**NomadSquad** is an intelligent travel planner built using **Python** and **Streamlit**, powered by the **Google Gemini API** and **Perplexity AI**.  
It combines creativity and practicality to generate *detailed*, *fun*, and *vibrant* itineraries that feel like they were written by your best travel buddy — not a bot.  

---

## ✨ Core Features

- 🎯 **Deep Customization** – Go beyond destination and duration. Choose your travel vibe, pace, food preferences, local transport style, and accommodation type.  
- 🤖 **Dynamic AI Persona** – “NomadSquad” responds like a witty, cheerful, travel-savvy friend — full of local slang, humor, and energy.  
- 💸 **Real-Time Currency Conversion** – Budget in your home currency, with automatic conversion to the destination currency.  
- ☀️ **Seasonal Intelligence** – The AI gives month-specific advice: weather info, ideal packing lists, and off/peak season tips.  
- 🗓️ **Structured, Fun Itineraries** – Three clearly formatted sections:  
  1. **Trip Overview & Seasonal Prep**  
  2. **Daily Adventure Itinerary**  
  3. **Essential Tips & Local Lingo**  
- 🧾 **PDF Export** – Download your complete travel plan as a stylish, ready-to-print PDF — no extra libraries required.  
- 🔗 **Perplexity Integration** – Fetches real booking and review links for hotels, stays, and activities in seconds.  
- 🧠 **Session Persistence** – Your generated trip stays on-screen even if Streamlit reloads or you switch tabs.  
- 🌙 **Dark Mode UI** – A beautifully styled, permanent dark-mode interface with modern animations and rounded elements.  
- 🔒 **Secure by Design** – All API keys are stored safely in `.streamlit/secrets.toml` (ignored by GitHub).  

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | Streamlit (Custom CSS for permanent dark mode) |
| **Backend** | Python |
| **AI Engine** | Google Gemini Pro API |
| **Data & Research** | Perplexity Sonar API |
| **Currency Conversion** | ExchangeRate-API |
| **PDF Generation** | Pillow (PIL) |
| **Deployment** | Streamlit Community Cloud + GitHub |

---

## 🚀 Run Locally

Follow these simple steps to set up NomadSquad on your local system 👇

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Ath-12/ai-planner-final.git
cd ai-planner-final
2️⃣ Create and Activate a Virtual Environment
Windows (PowerShell / CMD)

bash
Copy code
python -m venv venv
.\venv\Scripts\activate
Mac / Linux

bash
Copy code
python3 -m venv venv
source venv/bin/activate
3️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Add Your API Keys
Create a folder called .streamlit and inside it, make a file named secrets.toml:

bash
Copy code
mkdir .streamlit
Then open and edit:

bash
Copy code
nano .streamlit/secrets.toml
Add your keys:

toml
Copy code
GEMINI_API_KEY = "your_gemini_api_key_here"
PPLX_API_KEY = "your_perplexity_api_key_here"
EXCHANGE_RATE_API_KEY = "your_exchangerate_api_key_here"
⚠️ Note: secrets.toml is ignored by Git for security. Do not commit this file.

5️⃣ Run the App
bash
Copy code
streamlit run app.py
Then open your browser and go to:
👉 http://localhost:8501

🧩 Future Enhancements
🌅 Destination Hero Images (Unsplash integration for auto-image banners)

🧭 “Trip Presets” — Quick buttons for Romantic, Backpacker, Luxury, Foodie, and Offbeat modes

💾 Save multiple itineraries directly in the browser (local storage)

💬 Multi-language support for AI output (English, French, Spanish, Japanese)

🎭 “Serious / Funny” tone toggle for AI personality customization

🗺️ Interactive map view of itinerary stops

🤝 Contributing
Contributions are welcome!
If you have ideas for features, bug fixes, or UI improvements:

bash
Copy code
# Fork the repository
# Create your feature branch
git checkout -b feature/YourFeatureName

# Commit your changes
git commit -m "✨ Add: Your short feature description"

# Push to your branch
git push origin feature/YourFeatureName

# Create a Pull Request on GitHub
