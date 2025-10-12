import streamlit as st
import google.generativeai as genai
import os

# --- Function to get response from Gemini AI (Final Upgraded Prompt) ---
def get_ai_response(api_key, destination, duration, people, budget, travel_vibe, accommodation, pace):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro-latest')

    # Convert list inputs into clean, comma-separated strings
    accomm_str = ", ".join(accommodation)
    vibe_str = ", ".join(travel_vibe)

    # --- THE FINAL, MOST DETAILED PROMPT ---
    prompt = (
        f"You are a super-friendly and enthusiastic travel buddy who knows all the best local secrets. Your goal is to create an amazing and practical travel plan. Use a fun, encouraging tone and add relevant emojis! 🌴☀️"
        f"\n--- User's Trip Details ---"
        f"\nDestination: {destination}"
        f"\nDuration: {duration} days"
        f"\nNumber of People: {people}"
        f"\nBudget per Person per Day: Approximately ₹{budget}"
        f"\nPreferred Accommodation: {accomm_str}"
        f"\nDesired Travel Vibe: {vibe_str}"
        f"\nDesired Pace: {pace}"
        f"\n--- Itinerary Requirements ---"
        f"\n1.  **Daily Plan:** Create a logical and fun plan for each day."
        f"\n2.  **Accommodation Suggestions:** Suggest 1-2 specific, highly-rated, budget-friendly places that match their preference."
        f"\n3.  **Activities & Sightseeing:** Include a mix of activities that match the user's 'vibe'."
        f"    - If the vibe includes 'Adventure & Outdoors', suggest specific, exciting activities like scuba diving, parasailing, kayaking, or trekking to waterfalls."
        f"    - If the vibe includes '🎉 Partying' and the destination is known for nightlife (like Goa), suggest a few famous clubs or beach shacks with live music in a responsible way."
        f"    - If the vibe includes '🧘 Relaxation' or '⛪ Cultural Immersion', suggest visiting a significant local temple, ashram, or a peaceful place known for its serenity. For relevant locations, mention that some may offer simple accommodations for a unique and peaceful experience."
        f"\n4.  **Food Recommendations:** Suggest specific local eateries, not just types of food. Mention 1-2 must-try dishes."
        f"\n5.  **Transportation Deep Dive:** In the 'Details & Tips' section, provide a detailed breakdown of local transport. Mention estimated daily rental costs for scooters and cars, and the option to ask hotels for airport taxi arrangements."
        f"\n--- Output Format ---"
        f"\nStructure your entire response in three distinct sections, using '###' as a separator before each section header. Do not use '###' anywhere else."
        f"\n### Trip Overview: Start with a fun, exciting summary of the trip. Suggest the accommodations here."
        f"\n### Daily Itinerary: Provide the detailed, day-by-day plan in this section."
        f"\n### Details & Tips: Conclude with the 'Transportation Deep Dive' and other practical information."
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}."

# --- Page Configuration ---
st.set_page_config(
    page_title="Student AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# --- Load API Key from Streamlit Secrets ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("GEMINI_API_KEY not found! Please add it to your .streamlit/secrets.toml file.")
    st.stop()

# --- Main Application ---
st.title("✈️ Student AI Travel Planner")
st.markdown("Your intelligent assistant for creating personalized, budget-friendly trips!")

# --- User Input Form ---
with st.form("planner_form"):
    st.header("Tell me about your trip")

    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("📍 Destination", "Goa")
    with col2:
        duration = st.number_input("📅 Trip Duration (days)", min_value=1, value=5)

    col3, col4 = st.columns(2)
    with col3:
        budget = st.slider("💰 Budget per person per day (in ₹)", 1000, 10000, 2000, 500)
    with col4:
        num_people = st.number_input("👥 Number of People", min_value=1, value=3)

    st.subheader("What's your travel style?")
    travel_vibe = st.multiselect("Select your vibe:",
                                ["🎉 Partying", "🧘 Relaxation", "⛪ Cultural Immersion",
                                 "🏞️ Adventure & Outdoors", "🍽️ Foodie Focus", "💎 Offbeat & Hidden Gems"])

    col5, col6 = st.columns(2)
    with col5:
        accommodation = st.multiselect("🏨 Preferred Accommodation:",
                                       ["Hostel", "Budget Hotel", "Guesthouse", "Resort"])
    with col6:
        pace = st.select_slider("Select your travel pace:",
                                options=["Slow & Relaxed", "Moderate", "Fast-Paced & Packed"])

    submitted = st.form_submit_button("✨ Generate My Trip Plan")

# --- Generate and Display Itinerary ---
if submitted:
    with st.spinner("🤖 Your travel buddy is whipping up the perfect plan..."):
        ai_response = get_ai_response(
            api_key,
            destination,
            duration,
            num_people,
            budget,
            travel_vibe,
            accommodation,
            pace
        )
        st.markdown("---")
        st.subheader("🎉 Here is your personalized travel plan!")

        try:
            parts = ai_response.split("###")
            if len(parts) >= 4:
                overview = parts[1]
                itinerary = parts[2]
                details = parts[3]

                tab1, tab2, tab3 = st.tabs(["Trip Overview", "Daily Itinerary", "Details & Tips"])

                with tab1:
                    st.markdown(overview, unsafe_allow_html=True)
                with tab2:
                    st.markdown(itinerary, unsafe_allow_html=True)
                with tab3:
                    st.markdown(details, unsafe_allow_html=True)
            else:
                st.warning("Could not parse the AI response into tabs. Displaying full response below.")
                st.markdown(ai_response)

        except Exception as e:
            st.warning("An error occurred while parsing the response into tabs. Displaying full response below.")
            st.markdown(ai_response)