"""
Environmental & Community Health Explorer — entry point.

This file only sets up navigation between pages. Each page lives in views/
and owns its own topic. See README.md for the multipage layout and how to
add/edit a page without touching anyone else's file.
"""

import streamlit as st

st.set_page_config(
    page_title="Environmental & Community Health Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

home = st.Page("views/home.py", title="Overview", icon="🏠", default=True)
emissions_page = st.Page("views/emissions.py", title="Emissions (Mariah)", icon="🏭")
ses_page = st.Page("views/socioeconomic.py", title="Socioeconomic (Michelle)", icon="🏘️")
health_page = st.Page("views/health.py", title="Health & Pollution (Dalis)", icon="❤️")

pg = st.navigation([home, emissions_page, ses_page, health_page])
pg.run()
