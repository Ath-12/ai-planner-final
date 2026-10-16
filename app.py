import streamlit as st
from google import genai
from google.genai import types
import requests, datetime, re, time
from concurrent.futures import ThreadPoolExecutor
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
@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rate(home_currency="INR", dest_currency="USD"):
    """Return (rate, problem). rate is None when no live rate is available, so
    the app never shows a home-currency amount labelled as another currency."""
    if home_currency == dest_currency:
        return 1.0, None
    if not EXCHANGE_RATE_API_KEY:
        return None, "currency conversion is off (no EXCHANGE_RATE_API_KEY)"
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{home_currency}/{dest_currency}"
    try:
        r = requests.get(url, timeout=6); r.raise_for_status()
        data = r.json()
        if data.get("result") == "success" and data.get("conversion_rate"):
            return float(data["conversion_rate"]), None
        return None, f"the exchange-rate service said: {data.get('error-type', 'unknown error')}"
    except Exception:
        return None, "the exchange-rate service could not be reached"

def maps_search_url(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={up.quote(query)}"

def _links_from_perplexity(js: dict, k: int) -> list:
    """Perplexity has returned sources in different fields over time:
    `search_results` (title + url + date), older `citations` (plain URLs),
    and Markdown links inside the answer text. Read all of them."""
    links, seen = [], set()
    def add(url, title="", date=""):
        if url and url.startswith("http") and url not in seen:
            seen.add(url)
            links.append({"title": title or up.urlparse(url).netloc.removeprefix("www."), "url": url, "date": date or ""})
    for it in js.get("search_results") or []:
        add(it.get("url"), it.get("title"), it.get("date"))
    for url in js.get("citations") or []:
        add(url if isinstance(url, str) else url.get("url"))
    try:
        text = js["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        text = ""
    for title, url in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text):
        add(url, title)
    return links[:k]

def pplx_research(query: str, model: str = "sonar-pro", k: int = 8):
    """Return (links, problem). `problem` explains why there are no links, so the
    app can say so instead of silently showing an empty tab."""
    if not PPLX_API_KEY:
        return [], "Perplexity key (PPLX_API_KEY) is not set in the app's secrets."
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise, add trustworthy links (official or major OTAs), concise bullets."},
            {"role": "user", "content": f"Find high-quality booking pages and review links: {query}. Prefer official hotel sites or major OTAs. 6–8 best links."},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }
    try:
        r = requests.post("https://api.perplexity.ai/chat/completions",
                          headers={"Authorization": f"Bearer {PPLX_API_KEY}"}, json=payload, timeout=45)
        if r.status_code != 200:
            return [], f"Perplexity returned HTTP {r.status_code}: {r.text[:200]}"
        links = _links_from_perplexity(r.json(), k)
        return links, (None if links else "Perplexity answered but returned no links.")
    except Exception as e:
        return [], f"Perplexity request failed: {e}"

def quick_search_links(destination: str, stay_types: list) -> list:
    """Direct search pages built locally (no API, always available)."""
    q = up.quote_plus(destination)
    stays = " ".join(stay_types).lower()
    links = [
        ("Booking.com — hotels & stays", f"https://www.booking.com/searchresults.html?ss={q}"),
        ("Google Hotels — compare prices", f"https://www.google.com/travel/search?q={up.quote_plus('hotels in ' + destination)}"),
        ("Tripadvisor — reviews", f"https://www.tripadvisor.com/Search?q={q}"),
    ]
    if "airbnb" in stays or "apartment" in stays or "unique" in stays or not stay_types:
        links.insert(1, ("Airbnb — homes & unique stays", f"https://www.airbnb.com/s/{up.quote(destination)}/homes"))
    if "hostel" in stays:
        links.append(("Hostelworld — hostels", f"https://www.hostelworld.com/search?search_keywords={q}"))
    return [{"title": t, "url": u} for t, u in links]

# Google retires "preview" model names from time to time (that caused the
# 404 fixed in Jan 2026). The model can now be changed from Streamlit secrets
# without a code change, and a couple of stable fallbacks are tried in order.
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash"]

GEMINI_CONFIG = types.GenerateContentConfig(
    temperature=0.7,
    top_p=0.9,
    # Newer Gemini models "think" before answering and those tokens count
    # towards this limit, so it is set high enough for a full multi-day plan.
    max_output_tokens=8192,
    safety_settings=[
        types.SafetySetting(category=c, threshold="BLOCK_MEDIUM_AND_ABOVE")
        for c in ("HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                  "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")
    ],
)

@st.cache_resource
def gemini_client(api_key: str):
    return genai.Client(api_key=api_key)

def make_gemini_itinerary(client, prompt):
    """Return (plan_text, error_message). Tries the configured model first,
    then the fallbacks, so one retired model name doesn't take the app down."""
    errors = []
    for model in dict.fromkeys([GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]):
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=GEMINI_CONFIG)
        except Exception as e:
            errors.append(f"{model}: {e}")
            print(f"Gemini model '{model}' failed: {e}")   # visible in Streamlit Cloud logs
            continue
        text = (resp.text or "").strip()
        if not text:
            errors.append(f"{model}: empty response (possibly blocked by safety filters)")
            continue
        finish = getattr(resp.candidates[0], "finish_reason", None) if resp.candidates else None
        if str(finish).endswith("MAX_TOKENS"):
            text += "\n\n_(NomadSquad ran out of space here. Try fewer days for the full detail.)_"
        return text, None
    return None, "Gemini request failed. " + " | ".join(errors)


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

rate, rate_problem = get_exchange_rate(st.session_state.home_currency, st.session_state.dest_currency_select)
if rate is None:
    # No live rate: keep everything in the home currency rather than guess.
    st.session_state.exchange_rate = 1.0
    st.session_state.dest_currency = st.session_state.home_currency
else:
    st.session_state.exchange_rate = rate
    st.session_state.dest_currency = st.session_state.dest_currency_select

max_budget_home = 50000 if st.session_state.home_currency != "JPY" else 5000000
st.session_state.home_budget = st.slider(f"💰 Budget per person/day ({st.session_state.home_currency})", 100, max_budget_home, st.session_state.home_budget, 100)

converted_budget = st.session_state.home_budget * st.session_state.exchange_rate
st.markdown(f"👉 Approx. **{converted_budget:,.2f} {st.session_state.dest_currency}** per person/day")
if rate_problem:
    st.caption(f"⚠️ No live rate to {st.session_state.dest_currency_select}: {rate_problem}. "
               f"Your budget stays in {st.session_state.home_currency} and NomadSquad will plan with that.")
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
# Every plan is a paid AI call on a public app, so each visitor gets a short
# cooldown and a cap per session. (A visitor can reset it by reloading; the
# hard limit is the quota/budget set on the API key itself.)
MAX_PLANS_PER_SESSION = 5
COOLDOWN_SECONDS = 30
st.session_state.setdefault("plans_generated", 0)
st.session_state.setdefault("last_generated_at", 0.0)

if submitted:
    wait = COOLDOWN_SECONDS - (time.time() - st.session_state.last_generated_at)
    if not destination:
        st.error("🚨 Please enter a destination.")
    elif st.session_state.plans_generated >= MAX_PLANS_PER_SESSION:
        st.warning(f"🧳 You've planned {MAX_PLANS_PER_SESSION} trips this session. Come back later for more!")
    elif wait > 0:
        st.warning(f"⏳ Give NomadSquad {int(wait) + 1} more seconds before the next plan.")
    else:
        budget_for_ai = st.session_state.home_budget * st.session_state.exchange_rate
        dest_currency_for_ai = st.session_state.dest_currency

        with st.spinner("✨ NomadSquad is charting your adventure..."):
            prompt = build_prompt(
                destination, duration, num_people, budget_for_ai, dest_currency_for_ai,
                travel_vibe, accommodation, pace, origin_country, origin_city,
                transport_to_dest, travel_month, food_prefs, transport_prefs_local, special_requests
            )
            research_query = f"{destination} best {(', '.join(accommodation) or 'hotels')} near top sights, " \
                             f"booking pages and review links; min rating {min_rating}; must-have {', '.join(must_have) or 'none'}"
            # Both calls are slow network requests, so they run side by side.
            client = gemini_client(GEMINI_API_KEY)
            with ThreadPoolExecutor(max_workers=2) as pool:
                gem_future = pool.submit(make_gemini_itinerary, client, prompt)
                pplx_future = pool.submit(pplx_research, research_query, "sonar-pro")
                gem_text, gem_err = gem_future.result()
                links, links_problem = pplx_future.result()
            if links_problem:
                print(f"Booking links: {links_problem}")   # visible in Streamlit Cloud logs
            if gem_err:
                st.error(f"Gemini Error: {gem_err}")
            else:
                # ---- PERSIST ----
                st.session_state.final_output = gem_text
                st.session_state.links_output = links
                st.session_state.links_problem = links_problem
                st.session_state.plan_destination = destination
                st.session_state.plan_stays = accommodation
                st.session_state.plans_generated += 1
                st.session_state.last_generated_at = time.time()

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
    plan_dest = st.session_state.get("plan_destination") or destination or "Trip"

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
            st.markdown("**🔎 Picked by Perplexity from a live web search**")
            for it in links:
                date = f"  _{it['date']}_" if it.get("date") else ""
                st.markdown(f"- [{it['title']}]({it['url']}){date}")
        else:
            st.info("No AI-picked links this time"
                    + (f": {st.session_state.get('links_problem')}" if st.session_state.get("links_problem") else ".")
                    + " The direct searches below always work.")
        st.markdown("**🧭 Search directly**")
        for it in quick_search_links(plan_dest, st.session_state.get("plan_stays") or []):
            st.markdown(f"- [{it['title']}]({it['url']})")

    # Quick actions
    st.markdown("### Actions")
    st.link_button("🗺️ Open Destination in Google Maps", maps_search_url(plan_dest))
    pdf_bytes = cached_pdf(raw, f"NomadSquad — {plan_dest}")
    st.download_button(
        "⬇️ Download Itinerary (PDF)",
        data=pdf_bytes,
        file_name=f"NomadSquad_{re.sub(r'[^A-Za-z0-9]+', '_', plan_dest).strip('_')}.pdf",
        mime="application/pdf"
    )

    # Reset button for a fresh run
    if st.sidebar.button("🔄 Reset Trip"):
        st.session_state.final_output = None
        st.session_state.links_output = []
        st.rerun()

    # OPTIONAL: If you want to stop execution after rendering to avoid extra reruns:
    st.stop()
