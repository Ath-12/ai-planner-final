"""Automated checks for NomadSquad.

Runs app.py headlessly with Streamlit's built-in test runner. Gemini,
Perplexity and ExchangeRate-API are replaced with fakes, so no API keys or
internet are needed and nothing is billed.

Run:  pip install -r requirements-dev.txt  &&  pytest -q
"""
from pathlib import Path
from unittest import mock
import sys

import pytest
from streamlit.testing.v1 import AppTest
import google.genai as genai_mod

APP = str(Path(__file__).resolve().parents[1] / "app.py")
sys.path.insert(0, str(Path(APP).parent))   # so app.py can import pdf_export / calendar_export

PLAN = (
    "### 🎉 Your NomadSquad Trip Overview & Seasonal Intel! 🎉\nWarm, 30°C. Pack sunscreen 😎\n"
    "### 🗺️ Your Awesome 3-Day Adventure Itinerary! 🗺️\n"
    "**Day 1** Baga beach and sunset.\n**Day 2** Old Goa churches.\n**Day 3** Anjuna market.\n"
    "### ✨ NomadSquad's Pro Tips & Essential Info! ✨\nSussegad = the relaxed Goan way of life"
)


class FakeGemini:
    """Stands in for google.genai.Client. `fail_models` simulate retired models."""
    calls: list = []
    fail_models: set = set()
    text = PLAN

    def __init__(self, api_key):
        self.models = self

    def generate_content(self, model, contents, config):
        FakeGemini.calls.append(model)
        FakeGemini.last_prompt = contents
        if model in FakeGemini.fail_models:
            raise RuntimeError("404 NOT_FOUND")
        return mock.Mock(text=FakeGemini.text, candidates=[mock.Mock(finish_reason="STOP")])


def fake_post(perplexity_json=None, status=200):
    resp = mock.Mock(status_code=status, text="error body")
    resp.json.return_value = perplexity_json or {}
    return mock.Mock(return_value=resp)


@pytest.fixture(autouse=True)
def reset_fake():
    import streamlit as st
    st.cache_data.clear()        # results cached by one test must not leak into the next
    st.cache_resource.clear()
    FakeGemini.calls, FakeGemini.fail_models, FakeGemini.text = [], set(), PLAN


def run_app(secrets=None, post=None, rate_json=None):
    get = mock.Mock(side_effect=OSError("no network in tests")) if rate_json is None else \
        mock.Mock(return_value=mock.Mock(status_code=200, json=mock.Mock(return_value=rate_json),
                                         raise_for_status=mock.Mock()))
    patches = [mock.patch.object(genai_mod, "Client", FakeGemini),
               mock.patch("requests.get", get),
               mock.patch("requests.post", post or fake_post())]
    for p in patches:
        p.start()
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["GEMINI_API_KEY"] = "test"
    for k, v in (secrets or {}).items():
        at.secrets[k] = v
    at.run()
    return at, patches


def stop(patches):
    for p in patches:
        p.stop()


def generate(at, destination="Goa, India"):
    [t for t in at.text_input if "Destination" in str(t.label)][0].input(destination)
    [b for b in at.button if "Generate" in str(b.label)][0].click()
    at.run()
    return at


def tab_text(at, label):
    tab = [t for t in at.tabs if t.label == label][0]
    return " ".join(m.value for m in tab.markdown) + " " + " ".join(i.value for i in tab.info)


def test_generate_shows_three_sections_and_links_tab():
    at, p = run_app()
    try:
        generate(at)
        assert not at.exception
        assert [t.label for t in at.tabs] == ["Overview & Prep", "Daily Adventure", "Essential Tips", "🔗 Book & Reviews"]
        assert "Day 2" in tab_text(at, "Daily Adventure")
        assert "Day 2" not in tab_text(at, "Overview & Prep")
    finally:
        stop(p)


def test_falls_back_when_model_is_retired():
    FakeGemini.fail_models = {"gemini-3-flash-preview"}
    at, p = run_app()
    try:
        generate(at)
        assert not at.error
        assert FakeGemini.calls[:2] == ["gemini-3-flash-preview", "gemini-flash-latest"]
    finally:
        stop(p)


def test_reset_clears_plan_without_crashing():
    at, p = run_app()
    try:
        generate(at)
        [b for b in at.sidebar.button if "Reset" in str(b.label)][0].click()
        at.run()
        assert not at.exception
        at.run()                       # older test runners don't redraw after st.rerun()
        assert not at.exception
        assert not at.tabs
    finally:
        stop(p)


def test_links_tab_explains_missing_key_and_offers_direct_search():
    at, p = run_app()
    try:
        generate(at)
        text = tab_text(at, "🔗 Book & Reviews")
        assert "PPLX_API_KEY" in text
        assert "booking.com/searchresults.html?ss=Goa%2C+India" in text
    finally:
        stop(p)


@pytest.mark.parametrize("payload", [
    {"search_results": [{"title": "Taj Fort Aguada", "url": "https://www.tajhotels.com/aguada", "date": "2026-09-01"}],
     "choices": [{"message": {"content": "ok"}}]},
    {"citations": ["https://www.tajhotels.com/aguada"], "choices": [{"message": {"content": "ok"}}]},
    {"choices": [{"message": {"content": "Try [Taj Fort Aguada](https://www.tajhotels.com/aguada)."}}]},
])
def test_links_read_from_every_perplexity_format(payload):
    at, p = run_app(secrets={"PPLX_API_KEY": "test"}, post=fake_post(payload))
    try:
        generate(at)
        assert "https://www.tajhotels.com/aguada" in tab_text(at, "🔗 Book & Reviews")
    finally:
        stop(p)


def test_perplexity_error_is_explained():
    at, p = run_app(secrets={"PPLX_API_KEY": "test"}, post=fake_post(status=401))
    try:
        generate(at)
        assert "HTTP 401" in tab_text(at, "🔗 Book & Reviews")
    finally:
        stop(p)


def page_text(at):
    return " ".join(m.value for m in at.markdown) + " " + " ".join(c.value for c in at.caption)


def test_budget_stays_in_home_currency_without_a_live_rate():
    at, p = run_app()
    try:
        text = page_text(at)
        assert "2,000.00 INR" in text            # not mislabelled as USD
        assert "No live rate to USD" in text
    finally:
        stop(p)


def test_budget_is_converted_with_a_live_rate():
    at, p = run_app(secrets={"EXCHANGE_RATE_API_KEY": "test"},
                    rate_json={"result": "success", "conversion_rate": 0.012})
    try:
        text = page_text(at)
        assert "24.00 USD" in text
        assert "No live rate" not in text
    finally:
        stop(p)


def test_cooldown_blocks_rapid_repeat_and_cap_stops_spam():
    at, p = run_app()
    try:
        generate(at)
        generate(at, "Pune, India")                 # immediately again
        assert any("more seconds" in w.value for w in at.warning)
        assert len(FakeGemini.calls) == 1           # second click did not call the AI
        at.session_state["last_generated_at"] = 0.0
        at.session_state["plans_generated"] = 5
        generate(at, "Pune, India")
        assert any("planned 5 trips" in w.value for w in at.warning)
        assert len(FakeGemini.calls) == 1
    finally:
        stop(p)


def test_ai_text_is_not_rendered_as_html():
    FakeGemini.text = PLAN + '\n<img src=x onerror="alert(1)">'
    at, p = run_app()
    try:
        generate(at)
        for tab in at.tabs[:3]:
            assert all(not m.proto.allow_html for m in tab.markdown)
    finally:
        stop(p)


def test_tabs_survive_changed_headings_and_day_subheadings():
    FakeGemini.text = ("## 🌴 Trip Overview\nHot and humid.\n## 📅 Itinerary\n### Day 1\nBeach\n### Day 2\nFort\n"
                       "## 💡 Tips\nCarry cash.")
    at, p = run_app()
    try:
        generate(at)
        assert "Day 2" in tab_text(at, "Daily Adventure")
        assert "Carry cash" in tab_text(at, "Essential Tips")
        assert "Carry cash" not in tab_text(at, "Daily Adventure")
    finally:
        stop(p)


def test_prompt_includes_stay_filters_and_total_shown():
    at, p = run_app()
    try:
        generate(at)
        assert "minimum guest rating 4.2/5" in FakeGemini.last_prompt
        assert "Total budget for the group: about 30,000 INR (3 people x 5 days)" in FakeGemini.last_prompt
        assert "30,000 INR for 3 people × 5 days" in tab_text(at, "Overview & Prep")
    finally:
        stop(p)


def test_calendar_and_markdown_downloads():
    from calendar_export import build_ics, split_days
    from datetime import date
    at, p = run_app()
    try:
        generate(at)
        assert not at.exception
        assert "3 events" in " ".join(c.value for c in at.caption)
    finally:
        stop(p)
    days = split_days("**Day 1** Baga beach\nSwim\n**Day 2:** Old Goa\n### Day 3 — Market\nShop, eat; relax")
    assert [d for d, _ in days] == [1, 2, 3]
    ics = build_ics("**Day 1** Baga beach\n**Day 2** Fort", date(2026, 12, 20), "Goa, India").decode()
    assert ics.count("BEGIN:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20261220" in ics and "DTSTART;VALUE=DATE:20261221" in ics
    assert "Goa\\, India" in ics                          # commas escaped per RFC 5545
    assert all(len(l.encode()) <= 75 for l in ics.split("\r\n"))
