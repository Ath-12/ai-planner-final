✈️ NomadSquad - Your AI Travel Planner

Books in one hand, backpack in the other.

Live Demo: https://nomadsquad.streamlit.app/ 🚀

NomadSquad is an intelligent, personalized travel planner designed for the modern adventurer. Built with Python, Streamlit, and powered by the Google Gemini API, this application goes beyond generic suggestions to craft detailed, vibrant, and practical itineraries tailored to your unique travel style.

📸 Application Preview

(After taking a screenshot of your running application, you can simply drag and drop the image file here on the GitHub website to display it!)

✨ Core Features

NomadSquad is packed with features to make travel planning seamless and exciting:

Deep Customization: Go beyond just a destination and duration. Specify your travel vibe (from "Party & Nightlife" to "Relax & Recharge"), preferred accommodation, travel pace, food preferences, and more.

Dynamic AI Persona: The AI, "NomadSquad," acts as your enthusiastic travel buddy, providing fun, descriptive, and encouraging responses.

Real-Time Currency Conversion: A dedicated budget section allows you to set your budget in your home currency, with a real-time conversion display to your destination's currency.

Seasonal Intelligence: The AI provides crucial advice based on your month of travel, including typical weather, packing suggestions, and notes on peak vs. off-season travel.

Structured & Detailed Itineraries: The response is a full, multi-day plan broken down into three clear, tabbed sections:

Trip Overview & Seasonal Prep

Daily Adventure Itinerary

Essential Tips & Local Lingo

Vibrant, Fully-Styled UI: A beautiful, permanent dark-mode interface built with custom CSS for a professional and engaging user experience. All UI elements are styled for consistency and visual appeal.

Single-File, Secure Deployment: The entire application is self-contained in a single app.py file with embedded CSS, and it securely manages API keys for safe deployment on Streamlit Community Cloud.

🛠️ Tech Stack

Frontend: Streamlit

Backend & Core Logic: Python

Generative AI: Google Gemini Pro API

Currency Data: ExchangeRate-API

Deployment: Streamlit Community Cloud & GitHub

🚀 Running the Project Locally

To run this project on your own machine, follow these steps:

Clone the Repository:

git clone [https://github.com/Ath-12/ai-planner-final.git](https://github.com/Ath-12/ai-planner-final.git)
cd NomadSquad


Create and Activate a Virtual Environment:

python -m venv venv
venv\Scripts\activate


Install Dependencies:

pip install -r requirements.txt


Add Your API Keys:

Create a folder in the root directory named .streamlit.

Inside .streamlit, create a file named secrets.toml.

Add your API keys to this file in the following format:

GEMINI_API_KEY = "your_gemini_api_key_here"
EXCHANGE_RATE_API_KEY = "your_exchangerate_api_key_here"


Run the App:

streamlit run app.py
