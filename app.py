"""Streamlit front-end for the travel concierge Gemini pipeline.

Collects trip constraints in the sidebar, hands them to
generate.generate_itinerary_from_params (which builds the planning package,
calls Gemini, and saves a copy under output/ on the server), then renders
the result and offers it as a download to the visitor's own device.
"""
import os

import streamlit as st

# On Streamlit Community Cloud, secrets set in the dashboard land in
# st.secrets, not in the environment -- mirror them into os.environ so
# generate.py's os.environ / dotenv-based lookups keep working unchanged.
# Locally there's no secrets.toml at all (we use .env instead), and merely
# touching st.secrets in that case raises StreamlitSecretNotFoundError, so
# this whole block is best-effort.
try:
    for _key in ("GEMINI_API_KEY", "GROQ_API_KEY"):
        if _key in st.secrets and not os.environ.get(_key):
            os.environ[_key] = st.secrets[_key]
except st.errors.StreamlitSecretNotFoundError:
    pass

from generate import generate_itinerary_from_params, slugify

st.set_page_config(page_title="Travel Concierge", page_icon="🧭", layout="wide")

# Brand styling to match rishichellani.netlify.app (navy/teal, -apple-system stack).
# Theme colors (dark base, teal primary) come from .streamlit/config.toml; this
# covers the bits Streamlit's theme engine doesn't reach: fonts, buttons, and
# the custom header/footer.
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    }
    .concierge-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(14,165,233,0.12);
        border: 1px solid rgba(14,165,233,0.3);
        border-radius: 100px;
        padding: 0.375rem 1rem;
        font-size: 0.8125rem;
        color: #38bdf8;
        margin-bottom: 1rem;
        letter-spacing: 0.04em;
        font-weight: 500;
    }
    .concierge-badge::before { content: '●'; font-size: 0.5rem; }
    .concierge-title { font-size: 2.25rem; font-weight: 700; letter-spacing: -0.03em; margin-bottom: 0.25rem; }
    .concierge-title span { color: #0ea5e9; }
    .concierge-tagline { color: #94a3b8; font-size: 1rem; margin-bottom: 1.5rem; }

    div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: #0ea5e9 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background 0.2s, transform 0.15s !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background: #0284c7 !important;
        transform: translateY(-1px);
    }

    .concierge-footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(148,163,184,0.15);
        text-align: center;
        font-size: 0.8125rem;
        color: #64748b;
    }
    .concierge-footer a { color: #0ea5e9; text-decoration: none; font-weight: 600; }
    .concierge-footer a:hover { text-decoration: underline; }
    </style>

    <div class="concierge-badge">AI Travel Concierge</div>
    <div class="concierge-title">Plan your next trip with <span>Gemini</span></div>
    <p class="concierge-tagline">Tell us your constraints — get a day-by-day itinerary, grounded in real local highlights.</p>
    """,
    unsafe_allow_html=True,
)

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
                itinerary_md, saved_path, engine = generate_itinerary_from_params(
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
                st.session_state["engine"] = engine

if st.session_state.get("itinerary_md"):
    engine_label = {"gemini": "Gemini", "groq": "Groq (fallback)"}.get(
        st.session_state.get("engine"), st.session_state.get("engine")
    )
    st.success(f"Itinerary for **{st.session_state['destination']}** is ready! _(generated with {engine_label})_")
    st.download_button(
        "Download itinerary (.md)",
        data=st.session_state["itinerary_md"],
        file_name=f"{slugify(st.session_state['destination'])}_itinerary.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.markdown(st.session_state["itinerary_md"])
else:
    st.info("Fill out the trip details in the sidebar and click **Generate Itinerary** to begin.")

st.markdown(
    """
    <div class="concierge-footer">
      Built by <a href="https://rishichellani.netlify.app" target="_blank">Rishi Chellani</a>
      &nbsp;·&nbsp;
      <a href="https://github.com/rishichellani/travel-concierge" target="_blank">View on GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
