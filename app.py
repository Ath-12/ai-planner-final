import streamlit as st
import google.generativeai as genai
import os
import requests  # For currency conversion
import datetime  # To get current month as default
from PIL import Image

# ---
# FINAL APP.PY for NomadSquad
# This version includes all fixes and features:
# 1. Permanent Dark Mode (no toggle).
# 2. CSS is embedded directly in this file (no 'assets' folder needed).
# 3. All input boxes are styled to be circular, fixing UI overlap.
# 4. Currency conversion is now real-time, outside the main form.
# 5. The AI prompt is heavily refined to produce longer, more structured, and more fun responses.
# 6. "Destination Country" dropdown has been removed for flexibility.
# ---

# --- Initialize session state ---
if 'home_budget' not in st.session_state:
    st.session_state.home_budget = 2000
if 'exchange_rate' not in st.session_state:
    st.session_state.exchange_rate = 1.0
if 'dest_currency' not in st.session_state:
    st.session_state.dest_currency = "INR"
if 'home_currency' not in st.session_state:
    st.session_state.home_currency = "INR"
if 'dest_currency_select' not in st.session_state:
    st.session_state.dest_currency_select = "INR"

# --- FUNCTION TO LOAD EMBEDDED CSS ---
def load_embedded_css():
    """
    This function contains all the CSS for styling the app.
    It's embedded here to keep the project in a single file as requested.
    """
    css_styles = """
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    /* Define Color Variables (Dark Mode Focused) */
    :root {
        --primary-color: #FF6347; /* Tomato Orange */
        --accent-color: #FFD700; /* Gold */
        --link-color: #FFA500; /* Orange */
        --bg-dark: #001A33; /* Very Dark Navy */
        --secondary-bg-dark: #003366; /* Dark Navy */
        --text-dark: #FFE5CC; /* Light Peach */
        --subtle-border-dark: #004C99; /* Medium Navy */
    }

    /* General Styling & Permanent Dark Mode */
    body, .stApp {
        font-family: 'Poppins', sans-serif;
        background-color: var(--bg-dark) !important;
        color: var(--text-dark);
    }
    a { color: var(--link-color); text-decoration: none; transition: color 0.2s ease; }
    a:hover { color: var(--primary-color); text-decoration: underline; }

    .main .block-container {
        background-color: var(--secondary-bg-dark);
        border: 1px solid var(--subtle-border-dark);
        border-radius: 25px;
        padding: 2rem 2.5rem;
        box-shadow: 0 12px 45px rgba(0, 0, 0, 0.2);
        animation: fadeIn 0.6s ease-out;
    }
    h1, h2, h3 { color: var(--text-dark); font-weight: 700;}
    label { color: var(--text-dark) !important; font-weight: 600 !important; }

    /* --- UNIFIED CIRCULAR STYLING FOR ALL INPUTS --- */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stMultiselect"] > div[data-baseweb="select"] {
        background-color: var(--bg-dark) !important;
        border: 1px solid var(--subtle-border-dark) !important;
        color: var(--text-dark) !important;
        border-radius: 50px !important; /* Pill shape for ALL */
        transition: all 0.2s ease;
        padding-left: 20px !important; /* Consistent padding */
    }

    /* Input Focus Style (All Inputs) */
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stMultiSelect div[data-baseweb="select"]:focus-within,
    .stNumberInput input:focus {
         border-color: var(--primary-color) !important;
         box-shadow: 0 0 12px rgba(255, 99, 71, 0.5); /* Orange Glow */
    }
    
    /* Dropdown menu styling */
    div[data-baseweb="popover"] ul[role="listbox"] {
        background-color: var(--secondary-bg-dark) !important;
        border-radius: 15px !important;
        border: 1px solid var(--subtle-border-dark) !important;
    }
    div[data-baseweb="popover"] li[role="option"] { color: var(--text-dark) !important; }
    div[data-baseweb="popover"] li[aria-selected="true"] { background-color: var(--primary-color) !important; color: white !important; }
    div[data-baseweb="popover"] li:hover { background-color: rgba(255, 99, 71, 0.2) !important; }

    /* Main Generate Button */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(45deg, var(--primary-color), #FF8C00);
        color: white; border-radius: 50px; padding: 12px 35px;
        font-weight: 700; font-size: 17px; border: none;
        box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.25);
        transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        box-shadow: 0 0 30px var(--accent-color);
        transform: translateY(-4px) scale(1.03);
    }

    /* Tab Styling */
    div[data-baseweb="tab-list"] {
        display: flex; justify-content: center; border-bottom: none !important;
        margin-bottom: 2rem; padding: 6px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 50px;
    }
    button[data-baseweb="tab"] {
        font-size: 16px; font-weight: 600; padding: 12px 30px;
        border-radius: 50px; margin: 0 5px; border: none;
        background-color: transparent; color: var(--text-dark);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color);
        color: white !important;
        box-shadow: 0 5px 20px rgba(255, 99, 71, 0.5);
        transform: scale(1.05);
    }
    button[data-baseweb="tab"][aria-selected="false"]:hover {
       background-color: rgba(255, 99, 71, 0.15);
       color: var(--primary-color) !important;
       transform: translateY(-3px);
    }

    /* Layout & Animations */
    .stForm > div { gap: 1.2rem; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    .stSpinner > div > div {
        border-top-color: var(--primary-color) !important;
    }
    """
    st.markdown(f'<style>{css_styles}</style>', unsafe_allow_html=True)

load_embedded_css()

# --- Load API Keys ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    EXCHANGE_RATE_API_KEY = st.secrets.get("EXCHANGE_RATE_API_KEY", None)
except KeyError:
    st.error("GEMINI_API_KEY not found! Please add it to your .streamlit/secrets.toml file.")
    st.stop()


# --- Currency Conversion Function ---
@st.cache_data(ttl=3600)
def get_exchange_rate(home_currency="INR", dest_currency="USD"):
    if not EXCHANGE_RATE_API_KEY or home_currency == dest_currency:
        return 1.0, dest_currency
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{home_currency}/{dest_currency}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data.get("conversion_rate", 1.0), dest_currency
        else:
            # --- NEW: SHOW A WARNING TO THE USER ---
            st.warning(f"Could not fetch live exchange rate for {home_currency}/{dest_currency}. Using a default rate.")
            return 1.0, dest_currency
    except requests.exceptions.RequestException as e:
        # --- NEW: SHOW A WARNING TO THE USER ---
        st.warning(f"Could not fetch live exchange rate due to a network error. Using a default rate.")
        print(f"Error fetching exchange rate: {e}") # Keep this for your own logs
        return 1.0, dest_currency

# --- Function to get response from Gemini AI ---
def get_ai_response(api_key, destination, duration, people, budget_dest_currency, dest_currency_code, travel_vibe, accommodation, pace,
                    origin_country, origin_city, transport_to_dest, travel_month,
                    food_prefs, transport_prefs_local, special_requests):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro-latest')

    accomm_str = ", ".join(accommodation) if accommodation else "Any suitable"
    vibe_str = ", ".join(travel_vibe) if travel_vibe else "General Tourist"
    food_str = ", ".join(food_prefs) if food_prefs else "No specific preferences"

    # --- FINAL, MOST ROBUST PROMPT ---
    prompt = (
        f"You are NomadSquad, the ultimate AI travel companion! Your personality is adventurous, witty, and super enthusiastic. Your tagline is 'Books in one hand, backpack in the other.' Your goal is to generate an incredibly exciting, vibrant, practical, and personalized travel plan that makes the user feel like their adventure has already begun! Use a fun, encouraging tone, lots of relevant emojis (like 🗺️, ✈️, 🍜, 🏨, ✨), and rich, descriptive language."
        f"\n--- NomadSquad's Mission Briefing (User's Trip Details) ---"
        f"\nOrigin: {origin_city}, {origin_country}"
        f"\nDream Destination: {destination}"
        f"\nTime of Adventure: {travel_month}"
        f"\nTrip Length: {duration} glorious days"
        f"\nTravel Crew: {people} person(s)"
        f"\nDaily Budget Goal (per person): Approx. {budget_dest_currency:.0f} {dest_currency_code}"
        f"\nArrival Method: {transport_to_dest}"
        f"\nAccommodation Style: {accomm_str}"
        f"\nDesired Vibe: {vibe_str}"
        f"\nTravel Pace: {pace}"
        f"\nFoodie Preferences: {food_str}"
        f"\nLocal Transport Choice: {transport_prefs_local}"
        f"\nSpecial Requests / Must-Dos: {special_requests if special_requests else 'None'}"

        f"\n--- Your Itinerary Blueprint ---"
        f"\n**Be SUPER Descriptive & Fun!** Paint a vivid picture! Make recommendations sound irresistible!"
        f"\n**Flawlessly Blend ALL Preferences:** Create a cohesive plan reflecting ALL inputs."
        f"\n**Master of Seasons (Critical!):**"
        f"  - Vividly describe the weather AND atmosphere in {destination} during {travel_month} (Celsius)."
        f"  - Give specific packing advice."
        f"  - Explain the season type (Peak/Off/Shoulder) & impact."
        f"  - Suggest the *best* time to visit if different."

        f"\n1.  **Daily Plan:** A logical, exciting, detailed plan. Describe the *feeling* of places. Weave in Special Requests like hidden treasures."
        f"\n2.  **Accommodation:** Suggest 1-2 specific places matching style & budget (mention budget in {dest_currency_code}). Say *why* they rock."
        f"\n3.  **Activities:** Tailor activities richly to Vibe. Describe the *experience*. Include Must-Sees."
        f"\n4.  **Food Quest:** Recommend specific, mouth-watering eateries/dishes considering Food Prefs/Vibe. Describe vividly! Give budget hints in {dest_currency_code}."
        f"\n5.  **Getting Around:** Arrival options. *Example* generic links ONLY if origin/dest countries match. State clearly 'These are just starting points, check official sites!'. Local transport advice based on preference, costs in {dest_currency_code}, safety tips."
        f"\n6.  **Local Lingo:** Include a small section in the tips with 2-3 fun, useful local phrases or slang words with their meanings."

        f"\n--- **ABSOLUTELY CRITICAL OUTPUT FORMATTING** (Use EXACTLY this structure and do not stop early!) ---"
        f"### 🎉 Your NomadSquad Trip Overview & Seasonal Intel! 🎉\n"
        f"(Start with an super exciting, personalized intro paragraph. Then include all the Seasonal Context advice. Finally, list and describe the Accommodation Suggestions here. THIS SECTION MUST BE COMPLETE.)\n"
        f"### 🗺️ Your Awesome {duration}-Day Adventure Itinerary! 🗺️\n"
        f"(Provide the detailed, super descriptive day-by-day plan here. Use **Day X:** formatting. Be very descriptive and ensure you provide a full plan for all {duration} days. THIS SECTION MUST BE COMPLETE.)\n"
        f"### ✨ NomadSquad's Pro Tips & Essential Info! ✨\n"
        f"(Include the detailed Transportation advice: Arrival & Local. Add extra Budget-Saving Tips, Safety/Cultural pointers, and the fun 'Local Lingo' section. THIS SECTION MUST BE COMPLETE.)"
    )

    try:
        generation_config_args = {
            "max_output_tokens": 8192,
            "temperature": 0.8,
        }
        response = model.generate_content(prompt, generation_config=generation_config_args)

        if not response.parts:
            # Handle safety blocking
            block_reason = "Unknown"
            try:
                if response.prompt_feedback:
                    block_reason = response.prompt_feedback.block_reason.name
            except Exception: pass
            return f"⚠️ **Response Blocked!** Reason: {block_reason}. Please adjust your request."
        
        # Handle truncation
        finish_reason = "Unknown"
        is_truncated = False
        try:
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = response.candidates[0].finish_reason.name
                if finish_reason not in ["STOP", "FINISH_REASON_UNSPECIFIED"]:
                    is_truncated = True
        except Exception: pass
        
        clean_response = response.text
        if is_truncated:
            clean_response += f"\n\n⚠️ **Warning:** The AI response was cut short (stopped due to: {finish_reason}). It might have hit the maximum length limit. Try a shorter trip duration."
        
        return clean_response

    except Exception as e:
        return f"🚨 **Oops! Gemini Error:** {type(e).__name__} - {e}."


# --- Main Application UI ---
st.title("✈️ NomadSquad")
st.markdown("##### *Books in one hand, backpack in the other.*")
st.markdown("---")

# --- CURRENCY & BUDGET SECTION (Outside Form for Real-Time Update) ---
st.subheader("Your Origin & Budget 💸")
col_orig1, col_orig2 = st.columns(2)
with col_orig1:
    countries = ["India", "USA", "UK", "Canada", "Australia", "Germany", "France", "Japan", "Singapore", "UAE", "Thailand", "Italy", "Spain", "Mexico", "Brazil"]
    origin_country = st.selectbox("🌍 Your Origin Country", countries, index=0, key='origin_country_sel')
    currency_codes = ["INR", "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "SGD", "AED", "CHF", "CNY", "BRL", "MXN", "THB"]
    st.session_state.home_currency = st.selectbox("🏠 Your Home Currency", currency_codes, index=0, key='home_currency_sel')
with col_orig2:
    origin_city = st.text_input("🏙️ Your Origin City", placeholder="Enter Origin City...")
    # Destination currency is now inside the form, but we need a value for real-time conversion
    # Let's use a temporary selector here for the conversion logic
    st.session_state.dest_currency_select = st.selectbox("💲 Destination Currency (for conversion)", currency_codes, index=1, key='dest_currency_selector')

# Fetch rate and update session state
rate, actual_dest_code = get_exchange_rate(st.session_state.home_currency, st.session_state.dest_currency_select)
st.session_state.exchange_rate = rate
st.session_state.dest_currency = actual_dest_code

# Home Currency Slider with updated limit
max_budget_home = 50000
if st.session_state.home_currency == "JPY": max_budget_home = 5000000
st.session_state.home_budget = st.slider(f"💰 Budget per person/day ({st.session_state.home_currency})", 100, max_budget_home, st.session_state.home_budget, 100)

# Display Converted Budget Dynamically
converted_budget = st.session_state.home_budget * st.session_state.exchange_rate
st.markdown(f"👉 Approx. **{converted_budget:,.2f} {st.session_state.dest_currency}** per person/day")
st.markdown("---")

# --- MAIN FORM FOR OTHER INPUTS ---
with st.form("planner_form"):
    st.header("Tell NomadSquad About Your Dream Trip! ✨")

    # Destination input (single text box)
    destination = st.text_input("📍 Destination (City, Country)", placeholder="e.g., Paris, France")

    duration = st.number_input("📅 Trip Duration (days)", min_value=1, max_value=30, value=5)
    num_people = st.number_input("👥 Number of People", min_value=1, max_value=20, value=3)

    st.subheader("Your Journey Details 🗓️")
    col_jour1, col_jour2 = st.columns(2)
    with col_jour1:
         transport_to_dest = st.selectbox("✈️ How are you arriving?", ["Airplane", "Train", "Car", "Bus", "Not Sure Yet"])
    with col_jour2:
         current_month_index = datetime.datetime.now().month - 1
         months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
         travel_month = st.selectbox("📅 Month of Travel", months, index=current_month_index )

    st.subheader("Your Perfect Vibe ✨")
    travel_vibe = st.multiselect("🌈 Select your vibe(s):",
                                ["🎉 Party & Nightlife", "🧘 Relax & Recharge", "⛪ Culture & History", "🏞️ Adventure & Outdoors",
                                 "🍽️ Foodie Heaven", "🛍️ Shopping Spree", "💎 Offbeat & Hidden Gems", "📸 Picture Perfect Spots",
                                 "🎭 Arts & Theatre", "👩‍💻 Digital Nomad Work Spots", "👨‍👩‍👧‍👦 Family Friendly Fun", "💖 Romantic Getaway"],
                                 placeholder="Choose your travel style(s)")

    col_style1, col_style2 = st.columns(2)
    with col_style1:
        accommodation = st.multiselect("🏨 Preferred Stay:",
                                       [" hostels (Social & Budget)", " budget hotels (Private & Basic)", " guesthouses/Homestays (Local Feel)",
                                        " mid-range hotels (Comfort)", " boutique hotels (Stylish)", " luxury resorts (Pampering)",
                                        " airbnb/Apartments (Independent)", " unique Stays (Treehouse, Boat etc.)"],
                                        placeholder="Select accommodation type(s)")
    with col_style2:
        pace_options = ["🐢 Very Slow (1-2 things/day)", "🚶‍♀️ Relaxed (2-3 things/day)", "🏃‍♀️ Moderate (3-4 things/day)", "💨 Fast-Paced (Packed!)"]
        pace = st.select_slider("🏃 Travel Pace:", options=pace_options, value="🏃‍♀️ Moderate (3-4 things/day)")

    food_prefs = st.multiselect("🍜 Food Preferences?", ["Vegetarian", "Vegan", "Pescatarian", "Gluten-Free", " local cuisine MUST!",
                                                        " street food addict", " fine dining lover", " must try desserts",
                                                        " café hopping culture", " avoid spicy food"],
                                                        placeholder="Any dietary needs or food focus?")
    transport_prefs_local = st.selectbox("🛵 Preferred Local Transport?", ["Scooter/Bike Rental", "Car Rental (Self-Drive)",
                                                                         "Taxis/Ride-Sharing (Uber/Grab etc)", "Auto Rickshaws/Tuk-Tuks", "Public Transport (Bus/Metro/Train)", "Walking Focus"])
    special_requests = st.text_area("📝 Any Special Requests / Must-See Places?", placeholder="e.g., 'Must visit the Eiffel Tower at night!', 'Need info on accessible temples', 'Focus on surfing beaches only'")

    submitted = st.form_submit_button("🚀 Generate My Epic Trip Plan!")

# --- Generate and Display Itinerary ---
if submitted:
    if not destination:
         st.error("🚨 Please enter a destination to get started!")
    else:
        # Use the values from session state for budget/currency
        budget_for_ai = st.session_state.home_budget * st.session_state.exchange_rate
        dest_currency_for_ai = st.session_state.dest_currency

        with st.spinner("✨ NomadSquad is charting your adventure map... this is the exciting part! ✨"):
            ai_response = get_ai_response(
                GEMINI_API_KEY, destination, duration, num_people, budget_for_ai, dest_currency_for_ai,
                travel_vibe, accommodation, pace, origin_country, origin_city, transport_to_dest, travel_month,
                food_prefs, transport_prefs_local, special_requests
            )
            st.markdown("---")
            st.subheader("🎉 Your Awesome Personalized Travel Plan is Ready! 🎉")

            try:
                if ai_response.startswith("An error occurred") or ai_response.startswith("⚠️") or ai_response.startswith("🚨"):
                     st.error(ai_response)
                else:
                    parts = ai_response.split("###")
                    if len(parts) >= 3: # Check for at least 3 main sections
                        # Find parts by header text to make parsing robust
                        overview_text = ""
                        itinerary_text = ""
                        details_text = ""
                        
                        # A more robust way to find the text for each section
                        temp_response = ai_response
                        if "### 🎉 Your NomadSquad Trip Overview" in temp_response:
                            splits = temp_response.split("### 🗺️ Your Awesome", 1)
                            overview_text = splits[0].split("### 🎉 Your NomadSquad Trip Overview", 1)[-1]
                            temp_response = splits[1] if len(splits) > 1 else ""

                        if "### ✨ NomadSquad's Pro Tips" in temp_response:
                            splits = temp_response.split("### ✨ NomadSquad's Pro Tips", 1)
                            itinerary_text = splits[0]
                            details_text = splits[1] if len(splits) > 1 else ""
                        else: # Fallback if tips header is missing
                            itinerary_text = temp_response

                        if overview_text and itinerary_text and details_text:
                            tab1, tab2, tab3 = st.tabs(["Overview & Prep", "Daily Adventure", "Essential Tips"])
                            with tab1: st.markdown(overview_text, unsafe_allow_html=True)
                            with tab2: st.markdown(itinerary_text, unsafe_allow_html=True)
                            with tab3: st.markdown(details_text, unsafe_allow_html=True)
                        else:
                            st.warning("Hmm, NomadSquad got a bit too excited and didn't format the plan perfectly for tabs. Here's the full adventure plan:")
                            st.markdown(ai_response)
                    else:
                         st.warning("Hmm, NomadSquad's response wasn't structured for tabs. Here's the full adventure plan:")
                         st.markdown(ai_response)

            except Exception as e:
                st.warning("An error occurred while displaying the response in tabs. Showing the full response:")
                st.error(f"Display Error: {type(e).__name__} - {e}")
                st.markdown(ai_response)
