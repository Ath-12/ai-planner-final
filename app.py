import streamlit as st
import google.generativeai as genai
import requests, datetime
import urllib.parse as up
from pdf_export import build_pdf_bytes

# ======================
# Styling (your CSS kept)
# ======================
def load_embedded_css():
    css_styles = """
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    :root {
        --primary-color: #FF6347;
        --accent-color: #FFD700;
        --link-color: #FFA500;
        --bg-dark: #001A33;
        --secondary-bg-dark: #003366;
        --text-dark: #FFE5CC;
        --subtle-border-dark: #004C99;
    }
    body, .stApp { font-family: 'Poppins', sans-serif; background-color: var(--bg-dark) !important; color: var(--text-dark); }
    a { color: var(--link-color); text-decoration: none; transition: color 0.2s ease; }
    a:hover { color: var(--primary-color); text-decoration: underline; }
    .main .block-container {
        background-color: var(--secondary-bg-dark);
        border: 1px solid var(--subtle-border-dark);
        border-radius: 25px; padding: 2rem 2.5rem;
        box-shadow: 0 12px 45px rgba(0,0,0,0.2); animation: fadeIn 0.6s ease-out;
    }
    h1, h2, h3 { color: var(--text-dark); font-weight: 700; }
    label { color: var(--text-dark) !important; font-weight: 600 !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stMultiselect"] > div[data-baseweb="select"] {
        background-color: var(--bg-dark) !important;
        border: 1px solid var(--subtle-border-dark) !important;
        color: var(--text-dark) !important; border-radius: 50px !important;
        transition: all 0.2s ease; padding-left: 20px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus,
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stMultiSelect div[data-baseweb="select"]:focus-within, .stNumberInput input:focus {
        border-color: var(--primary-color) !important; box-shadow: 0 0 12px rgba(255,99,71,.5);
    }
    div[data-baseweb="popover"] ul[role="listbox"] {
        background-color: var(--secondary-bg-dark) !important; border-radius: 15px !important;
        border: 1px solid var(--subtle-border-dark) !important;
    }
    div[data-baseweb="popover"] li[role="option"] { color: var(--text-dark) !important; }
    div[data-baseweb="popover"] li[aria-selected="true"] { background-color: var(--primary-color) !important; color: white !important; }
    div[data-baseweb="popover"] li:hover { background-color: rgba(255,99,71,0.2) !important; }
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(45deg, var(--primary-color), #FF8C00);
        color: white; border-radius: 50px; padding: 12px 35px;
        font-weight: 700; font-size: 17px; border: none;
        box-shadow: 0 6px 20px rgba(0,0,0,.25); transition: all .35s cubic-bezier(.175,.885,.32,1.275);
        cursor: pointer;
    }
    div[data-testid="stFormSubmitButton"] button:hover { box-shadow: 0 0 30px var(--accent-color); transform: translateY(-4px) scale(1.03); }
    div[data-baseweb="tab-list"] {
        display:flex; justify-content:center; border-bottom:none !important; margin-bottom:2rem; padding:6px;
        background-color: rgba(255,255,255,0.05); border-radius:50px;
    }
    button[data-baseweb="tab"] {
        font-size:16px; font-weight:600; padding:12px 30px; border-radius:50px; margin:0 5px; border:none;
        background:transparent; color:var(--text-dark); transition:all .4s cubic-bezier(.175,.885,.32,1.275);
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color:var(--primary-color); color:white !important; box-shadow:0 5px 20px rgba(255,99,71,.5); transform:scale(1.05);
    }
    button[data-baseweb="tab"][aria-selected="false"]:hover {
        background-color:rgba(255,99,71,.15); color:var(--primary-color) !important; transform: translateY(-3px);
    }
    .stForm > div { gap:1.2rem; }
    @keyframes fadeIn { from {opacity:0; transform:translateY(15px);} to {opacity:1; transform:translateY(0);} }
    .stSpinner > div > div { border-top-color: var(--primary-color) !important; }
    """
    st.markdown(f"<style>{css_styles}</style>", unsafe_allow_html=True)

load_embedded_css()

# ======================
# API KEYS
# ======================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("GEMINI_API_KEY not found in .streamlit/secrets.toml")
    st.stop()

PPLX_API_KEY = st.secrets.get("PPLX_API_KEY")
EXCHANGE_RATE_API_KEY = st.secrets.get("EXCHANGE_RATE_API_KEY")

# ======================
# SESSION STATE (PERSISTENCE)
# ======================
if "home_budget" not in st.session_state: st.session_state.home_budget = 2000
if "exchange_rate" not in st.session_state: st.session_state.exchange_rate = 1.0
if "dest_currency" not in st.session_state: st.session_state.dest_currency = "INR"
if "home_currency" not in st.session_state: st.session_state.home_currency = "INR"
if "dest_currency_select" not in st.session_state: st.session_state.dest_currency_select = "INR"

# Persist generated outputs
if "final_output" not in st.session_state: st.session_state.final_output = None
if "links_output" not in st.session_state: st.session_state.links_output = []

# ======================
# HELPERS
# ======================
@st.cache_data(ttl=3600)
def get_exchange_rate(home_currency="INR", dest_currency="USD"):
    if not EXCHANGE_RATE_API_KEY or home_currency == dest_currency:
        return 1.0, dest_currency
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{home_currency}/{dest_currency}"
    try:
        r = requests.get(url, timeout=6); r.raise_for_status()
        data = r.json()
        if data.get("result") == "success": return data.get("conversion_rate", 1.0), dest_currency
        st.warning("Could not fetch live exchange rate. Using 1.0")
    except Exception:
        st.warning("Network error fetching exchange rate. Using 1.0")
    return 1.0, dest_currency

def maps_search_url(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={up.quote(query)}"

def pplx_research(query:str, model:str="sonar-pro", k:int=8):
    if not PPLX_API_KEY: return "", []
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {PPLX_API_KEY}", "Content-Type":"application/json"}
    payload = {
        "model": model,  # "sonar-pro" (fast) or "sonar-deep-research" (deeper)
        "messages": [
            {"role":"system","content":"Be precise, add trustworthy links (official or major OTAs), concise bullets."},
            {"role":"user","content": f"Find high-quality booking pages and review links: {query}. Prefer official hotel sites or major OTAs. 6–8 best links."}
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1200
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        js = r.json()
        text = js["choices"][0]["message"]["content"]
        results = js.get("search_results", []) or []
        links = []
        for it in results[:k]:
            links.append({"title": it.get("title","Link"), "url": it.get("url","#"), "date": it.get("date","")})
        return text, links
    except Exception as e:
        st.info(f"Perplexity research unavailable ({e})."); return "", []

def make_gemini_itinerary(api_key, prompt):
    try:
        genai.configure(api_key=api_key)

        # ✅ UPDATED: Using your available Gemini 3 Flash model
        # This is the best balance of speed and intelligence for your app right now.
        model_name = "models/gemini-3-flash-preview"
        model = genai.GenerativeModel(model_name)

        cfg = {
            "max_output_tokens": 4096,  # Increased for detailed itineraries
            "temperature": 0.7,
            "top_p": 0.9
        }

        # Safety settings to prevent blocking of travel content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        resp = model.generate_content(
            prompt, 
            generation_config=cfg,
            safety_settings=safety_settings
        )

        if not resp or not getattr(resp, "text", None):
            return None, "Empty response from Gemini."

        return resp.text.strip(), None

    except Exception as e:
        # Debug block kept in case you ever need to check models again
        try:
            print(f"❌ Error with model '{model_name}': {e}")
            print("🔍 Listing available models for your key...")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"   - {m.name}")
        except:
            pass
        return None, f"Gemini request failed: {e}"
    

@st.cache_data(show_spinner=False)
def cached_pdf(markdown_text: str, title: str) -> bytes:
    """Build the PDF once per plan instead of on every rerun."""
    return build_pdf_bytes(markdown_text, title)

# ======================
# UI: Title
# ======================
st.title("✈️ NomadSquad")
st.markdown("##### *Books in one hand, backpack in the other.*")
st.markdown("---")

# ======================
# ORIGIN & BUDGET
# ======================
st.subheader("Your Origin & Budget 💸")
col1, col2 = st.columns(2)
with col1:
    countries = ["India","USA","UK","Canada","Australia","Germany","France","Japan","Singapore","UAE","Thailand","Italy","Spain","Mexico","Brazil"]
    origin_country = st.selectbox("🌍 Your Origin Country", countries, index=0, key='origin_country_sel')
    currency_codes = ["INR","USD","EUR","GBP","CAD","AUD","JPY","SGD","AED","CHF","CNY","BRL","MXN","THB"]
    st.session_state.home_currency = st.selectbox("🏠 Your Home Currency", currency_codes, index=0, key='home_currency_sel')
with col2:
    origin_city = st.text_input("🏙️ Your Origin City", placeholder="Enter Origin City...")
    st.session_state.dest_currency_select = st.selectbox("💲 Destination Currency (for conversion)", currency_codes, index=1, key='dest_currency_selector')

rate, actual_dest_code = get_exchange_rate(st.session_state.home_currency, st.session_state.dest_currency_select)
st.session_state.exchange_rate = rate
st.session_state.dest_currency = actual_dest_code

max_budget_home = 50000 if st.session_state.home_currency != "JPY" else 5000000
st.session_state.home_budget = st.slider(f"💰 Budget per person/day ({st.session_state.home_currency})", 100, max_budget_home, st.session_state.home_budget, 100)

converted_budget = st.session_state.home_budget * st.session_state.exchange_rate
st.markdown(f"👉 Approx. **{converted_budget:,.2f} {st.session_state.dest_currency}** per person/day")
st.link_button("🗺️ Open Destination in Google Maps", maps_search_url(origin_city or "Your city"))
st.markdown("---")

# ======================
# FORM
# ======================
with st.form("planner_form"):
    st.header("Tell NomadSquad About Your Dream Trip! ✨")
    destination = st.text_input("📍 Destination (City, Country)", placeholder="e.g., Paris, France")
    duration = st.number_input("📅 Trip Duration (days)", min_value=1, max_value=30, value=5)
    num_people = st.number_input("👥 Number of People", min_value=1, max_value=20, value=3)

    st.subheader("Your Journey Details 🗓️")
    c1, c2 = st.columns(2)
    with c1:
        transport_to_dest = st.selectbox("✈️ How are you arriving?", ["Airplane","Train","Car","Bus","Not Sure Yet"])
    with c2:
        current_month_index = datetime.datetime.now().month - 1
        months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        travel_month = st.selectbox("📅 Month of Travel", months, index=current_month_index)

    st.subheader("Your Perfect Vibe ✨")
    travel_vibe = st.multiselect(
        "🌈 Select your vibe(s):",
        ["🎉 Party & Nightlife","🧘 Relax & Recharge","⛪ Culture & History","🏞️ Adventure & Outdoors",
         "🍽️ Foodie Heaven","🛍️ Shopping Spree","💎 Offbeat & Hidden Gems","📸 Picture Perfect Spots",
         "🎭 Arts & Theatre","👩‍💻 Digital Nomad Work Spots","👨‍👩‍👧‍👦 Family Friendly Fun","💖 Romantic Getaway"]
    )

    col_style1, col_style2 = st.columns(2)
    with col_style1:
        accommodation = st.multiselect(
            "🏨 Preferred Stay:",
            ["hostels (Social & Budget)","budget hotels (Private & Basic)","guesthouses/Homestays (Local Feel)",
             "mid-range hotels (Comfort)","boutique hotels (Stylish)","luxury resorts (Pampering)",
             "airbnb/Apartments (Independent)","unique Stays (Treehouse, Boat etc.)"]
        )
    with col_style2:
        pace = st.radio("🏃 Travel Pace", ["🐢 Very Slow","🚶 Relaxed","🏃 Moderate","💨 Fast"], horizontal=True)

    food_prefs = st.multiselect(
        "🍜 Food Preferences?",
        ["Vegetarian","Vegan","Pescatarian","Gluten-Free","local cuisine MUST!","street food addict",
         "fine dining lover","must try desserts","café hopping culture","avoid spicy food"]
    )
    transport_prefs_local = st.selectbox(
        "🛵 Preferred Local Transport?",
        ["Scooter/Bike Rental","Car Rental (Self-Drive)","Taxis/Ride-Sharing (Uber/Grab etc)","Auto Rickshaws/Tuk-Tuks",
         "Public Transport (Bus/Metro/Train)","Walking Focus"]
    )

    with st.popover("Advanced filters"):
        min_rating = st.slider("Minimum hotel rating", 3.0, 5.0, 4.2, 0.1)
        must_have = st.multiselect("Must-have amenities", ["Wi-Fi","Breakfast","Pool","Kitchen","Gym"])

    special_requests = st.text_area("📝 Any Special Requests / Must-See Places?",
                                    placeholder="e.g., 'Eiffel Tower at night', 'Accessible temples', 'Surfing only'")

    submitted = st.form_submit_button("🚀 Generate My Epic Trip Plan!")

# ======================
# PROMPT (funny + lingo + month packing)
# ======================
def build_prompt(destination, duration, people, budget_dest_currency, dest_currency_code, travel_vibe, accommodation, pace,
                 origin_country, origin_city, transport_to_dest, travel_month, food_prefs, transport_prefs_local, special_requests):
    accomm_str = ", ".join(accommodation) if accommodation else "Any suitable"
    vibe_str   = ", ".join(travel_vibe) if travel_vibe else "General Tourist"
    food_str   = ", ".join(food_prefs) if food_prefs else "No specific preferences"
    prompt = (
        f"You are NomadSquad, an adventurous, witty, emoji-loving travel planner. Lean funny and friendly.\n"
        f"Add plenty of destination lingo and local slang with brief meanings (5–10 phrases sprinkled naturally).\n"
        f"Include playful jokes and hype, but stay practical and accurate.\n"
        f"--- TRIP INPUTS ---\n"
        f"Origin: {origin_city}, {origin_country}\n"
        f"Destination: {destination}\n"
        f"Month: {travel_month}\n"
        f"Duration: {duration} days\n"
        f"People: {people}\n"
        f"Daily Budget (per person): {budget_dest_currency:.0f} {dest_currency_code}\n"
        f"Arrival: {transport_to_dest}\n"
        f"Stay: {accomm_str}\n"
        f"Vibe: {vibe_str}\n"
        f"Pace: {pace}\n"
        f"Food: {food_str}\n"
        f"Local Transport Pref: {transport_prefs_local}\n"
        f"Requests: {special_requests or 'None'}\n"
        f"--- RULES ---\n"
        f"1) In the OVERVIEW, give seasonal/weather context for {destination} in {travel_month} (°C), "
        f"and a concise PACKING LIST tailored to the season (e.g., rain gear in monsoon, layers in winter, sunscreen in summer).\n"
        f"2) DAILY ITINERARY: Write a vivid day-by-day plan (**Day 1**, **Day 2**, ...). Blend vibes & requests; be descriptive and fun.\n"
        f"3) TIPS: Include arrival & local transport guidance, safety, budget hacks, and a 'Local Lingo' mini-glossary "
        f"(5–10 short entries: phrase = meaning + when to use).\n"
        f"4) FOOD: Suggest specific eateries/dishes respecting preferences; add price hints in {dest_currency_code}.\n"
        f"5) ACCOMMODATION: Suggest 1–2 options that match style & budget with brief WHY they fit.\n"
        f"6) Keep it structured EXACTLY in these headings:\n"
        f"### 🎉 Your NomadSquad Trip Overview & Seasonal Intel! 🎉\n"
        f"### 🗺️ Your Awesome {duration}-Day Adventure Itinerary! 🗺️\n"
        f"### ✨ NomadSquad's Pro Tips & Essential Info! ✨\n"
        f"End each section with one fun one-liner in local flavor."
    )
    return prompt

# ======================
# GENERATE (writes to session_state)
# ======================
if submitted:
    if not destination:
        st.error("🚨 Please enter a destination.")
    else:
        budget_for_ai = st.session_state.home_budget * st.session_state.exchange_rate
        dest_currency_for_ai = st.session_state.dest_currency

        with st.spinner("✨ NomadSquad is charting your adventure..."):
            prompt = build_prompt(
                destination, duration, num_people, budget_for_ai, dest_currency_for_ai,
                travel_vibe, accommodation, pace, origin_country, origin_city,
                transport_to_dest, travel_month, food_prefs, transport_prefs_local, special_requests
            )
            gem_text, gem_err = make_gemini_itinerary(GEMINI_API_KEY, prompt)
            if gem_err:
                st.error(f"Gemini Error: {gem_err}")
            else:
                # Perplexity research (optional, shows links)
                research_query = f"{destination} best {(', '.join(accommodation) or 'hotels')} near top sights, " \
                                 f"booking pages and review links; min rating {min_rating}; must-have {', '.join(must_have) or 'none'}"
                _, links = pplx_research(research_query, model="sonar-pro")

                # ---- PERSIST ----
                st.session_state.final_output = gem_text
                st.session_state.links_output = links

                st.success("Trip generated! Scroll down to view.")

# ======================
# RENDER FROM SESSION (persists across reruns)
# ======================
if st.session_state.final_output:
    st.markdown("---")
    st.subheader("🎉 Your Awesome Personalized Travel Plan is Ready! 🎉")

    # Tabs: Overview / Itinerary / Tips / Links
    tab_titles = ["Overview & Prep","Daily Adventure","Essential Tips","🔗 Book & Reviews"]
    t1, t2, t3, t4 = st.tabs(tab_titles)

    raw = st.session_state.final_output
    links = st.session_state.links_output or []

    # split by headers
    overview, itinerary, tips = "", "", ""
    if "### 🎉 Your NomadSquad Trip Overview" in raw and "### 🗺️" in raw:
        overview = raw.split("### 🗺️",1)[0].split("### 🎉",1)[-1]
        rest = "### 🗺️" + raw.split("### 🗺️",1)[1]
        if "### ✨" in rest:
            itinerary = rest.split("### ✨",1)[0]
            tips = "### ✨" + rest.split("### ✨",1)[1]
        else:
            itinerary = rest

    with t1: st.markdown(overview or raw, unsafe_allow_html=True)
    with t2: st.markdown(itinerary or raw, unsafe_allow_html=True)
    with t3: st.markdown(tips or raw, unsafe_allow_html=True)
    with t4:
        if links:
            for it in links:
                st.markdown(f"- [{it['title']}]({it['url']})  _{it.get('date','')}_")
        else:
            st.info("No external links were added. Try again later or adjust filters.")

    # Quick actions
    st.markdown("### Actions")
    st.link_button("🗺️ Open Destination in Google Maps", maps_search_url(destination or ""))
    pdf_bytes = cached_pdf(raw, f"NomadSquad — {destination or 'Trip'}")
    st.download_button(
        "⬇️ Download Itinerary (PDF)",
        data=pdf_bytes,
        file_name=f"NomadSquad_{(destination or 'Trip').replace(',','').replace(' ','_')}.pdf",
        mime="application/pdf"
    )

    # Reset button for a fresh run
    if st.sidebar.button("🔄 Reset Trip"):
        st.session_state.final_output = None
        st.session_state.links_output = []
        st.rerun()

    # OPTIONAL: If you want to stop execution after rendering to avoid extra reruns:
    st.stop()
