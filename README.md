# ✈️ NomadSquad — AI Travel Planner

> **Books in one hand, backpack in the other.**
> Fill in one form, get a complete, personalised trip plan: seasonal prep, a day-by-day itinerary, local tips, booking links, a PDF and a calendar file.

[![tests](https://github.com/Ath-12/ai-planner-final/actions/workflows/tests.yml/badge.svg)](https://github.com/Ath-12/ai-planner-final/actions/workflows/tests.yml)

🌍 **Live demo:** https://nomadsquad.streamlit.app/
_Hosted on Streamlit Community Cloud's free tier. If the app has been idle it shows "Wake up this app": click it and give it about a minute._

---

## ✨ What it does

- **One detailed form**: destination, days, group size, travel month, how you're arriving, vibes, stay type, pace, food preferences, local transport, hotel rating and amenities, special requests.
- **Budget in your own currency**: a daily budget in your home currency, converted live to the destination currency (ExchangeRate-API). If no live rate is available, the budget stays in your currency and the app says so.
- **AI itinerary (Google Gemini)**: a structured prompt makes the plan come back in three sections, shown as tabs:
  1. Trip overview & seasonal intel: weather for that month and a packing list
  2. Day-by-day adventure itinerary
  3. Pro tips: transport, safety, budget hacks and a "local lingo" mini-glossary
- **Travel-buddy persona**: witty, emoji-friendly, with local slang explained.
- **Booking & reviews**: real links picked by Perplexity from a live web search, plus direct searches on Booking.com, Google Hotels, Airbnb, Tripadvisor and Hostelworld that always work.
- **Estimated total budget** for the whole group and trip.
- **Exports**: a clean PDF (proper Unicode font, so ₹, accents and dashes print correctly), a Markdown file, and a **calendar file (.ics)** with one event per itinerary day for Google Calendar, Apple Calendar or Outlook.
- **Fair use**: a 30-second cooldown and 5 plans per visitor session, so the public demo can't burn through the API quota.

## 🧠 How it works

```
Browser ──► app.py (Python + Streamlit, on Streamlit Community Cloud)
              ├─► ExchangeRate-API     currency rate (cached 1 hour)
              ├─► Google Gemini        writes the plan          ┐ run at the
              └─► Perplexity Sonar     finds real booking links ┘ same time
```

- No database and no login: a plan lives only in the visitor's session.
- API keys stay on the server (Streamlit secrets) and are never sent to the browser.
- The Gemini model can be changed with the `GEMINI_MODEL` secret; if it is unavailable, the app tries `gemini-flash-latest` and `gemini-2.5-flash` before showing an error.

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| App (UI + server) | Python, Streamlit, custom CSS dark theme |
| AI itinerary | Google Gemini via the `google-genai` SDK |
| Booking links | Perplexity Sonar API |
| Currency | ExchangeRate-API |
| PDF | fpdf2 + DejaVu Sans font |
| Calendar | iCalendar (.ics), generated in `calendar_export.py` |
| Tests | pytest + Streamlit `AppTest`, run by GitHub Actions |
| Hosting | Streamlit Community Cloud |

## 🚀 Run it locally

**1. Clone**

```bash
git clone https://github.com/Ath-12/ai-planner-final.git
cd ai-planner-final
```

**2. Create a virtual environment and install**

```bash
python -m venv venv
# Windows:      .\venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
```

**3. Add your keys**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` and fill in at least `GEMINI_API_KEY`. `PPLX_API_KEY` and `EXCHANGE_RATE_API_KEY` are optional; the app works without them and tells you what's missing. `secrets.toml` is git-ignored.

**4. Run**

```bash
streamlit run app.py
```

Then open http://localhost:8501.

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The tests run the real `app.py` with Gemini, Perplexity and ExchangeRate-API replaced by fakes, so they need no keys, no internet, and cost nothing.

## 📁 Project structure

```
app.py                  UI, form, prompt, AI calls, results tabs
pdf_export.py           Plan → PDF
calendar_export.py      Itinerary → .ics calendar file
fonts/                  DejaVu Sans (open licence, see LICENSE-DejaVu.txt)
tests/test_app.py       Automated tests
.streamlit/config.toml  Theme
.streamlit/secrets.toml.example   Key names (copy to secrets.toml)
```

## 🧩 Ideas for later

- Map view of each day's stops
- Save and compare several trips
- Multi-language plans
- Ask Gemini for structured JSON instead of Markdown sections

## 👨‍💻 Author

**Atharva Palsuledesai** · [@Ath-12](https://github.com/Ath-12)
