"""Streamlit front-end for the travel concierge Gemini pipeline.

Collects trip constraints in the sidebar, hands them to
generate.generate_itinerary_from_params (which builds the planning package,
calls Gemini, and saves a copy under output/), then renders the result.
"""
import os

import streamlit as st

# On Streamlit Community Cloud, secrets set in the dashboard land in
# st.secrets, not in the environment -- mirror them into os.environ so
# generate.py's os.environ / dotenv-based lookups keep working unchanged.
for _key in ("GEMINI_API_KEY", "GROQ_API_KEY"):
    if _key in st.secrets and not os.environ.get(_key):
        os.environ[_key] = st.secrets[_key]

from generate import generate_itinerary_from_params

st.set_page_config(page_title="Travel Concierge", page_icon="🧭", layout="wide")

FOCUS_OPTIONS = [
    "Food",
    "Culture",
    "Adventure",
    "Relaxation",
    "Nightlife",
    "Shopping",
    "Nature",
    "Family-Friendly",
]

st.title("🧭 AI Travel Concierge")
st.caption("Tell us your constraints — Gemini builds the day-by-day plan.")

with st.sidebar:
    st.header("Trip Details")
    with st.form("trip_form"):
        destination = st.text_input("Destination City", placeholder="e.g. Kyoto, Japan")
        travelers = st.number_input("Number of Travelers", min_value=1, max_value=20, value=2, step=1)
        duration = st.number_input("Trip Duration (days)", min_value=1, max_value=30, value=5, step=1)
        budget = st.selectbox("Budget Level", ["Budget", "Moderate", "Luxury"], index=1)
        focus = st.multiselect("Trip Focus", FOCUS_OPTIONS, default=["Culture"])
        must_haves = st.text_area(
            "Must-See / Must-Do (optional)",
            placeholder="e.g. Joe's Pizza, a morning walk through Central Park, sunset at the Top of the Rock",
            help="Specific places, activities, or experiences the itinerary must include. One per line or comma-separated.",
        )
        submitted = st.form_submit_button("Generate Itinerary", use_container_width=True)

if submitted:
    if not destination.strip():
        st.error("Please enter a destination city.")
    elif not focus:
        st.error("Please select at least one trip focus.")
    else:
        with st.spinner(f"Consulting Gemini to plan your trip to {destination.strip()}..."):
            try:
                itinerary_md, saved_path = generate_itinerary_from_params(
                    city=destination,
                    travelers=int(travelers),
                    duration=int(duration),
                    budget=budget,
                    focus=focus,
                    must_haves=must_haves,
                )
            except Exception as exc:
                st.session_state.pop("itinerary_md", None)
                st.error(f"Failed to generate itinerary: {exc}")
            else:
                st.session_state["itinerary_md"] = itinerary_md
                st.session_state["saved_path"] = str(saved_path)
                st.session_state["destination"] = destination.strip()

if st.session_state.get("itinerary_md"):
    st.success(f"Itinerary for **{st.session_state['destination']}** saved to `{st.session_state['saved_path']}`")
    st.markdown(st.session_state["itinerary_md"])
else:
    st.info("Fill out the trip details in the sidebar and click **Generate Itinerary** to begin.")
