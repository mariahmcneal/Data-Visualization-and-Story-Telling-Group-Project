import streamlit as st
from data_utils import load_data, VARIABLE_GROUPS

df = load_data()

title_col, img_col = st.columns([0.8, 1.2])
with title_col:
    st.title("Environmental & Community Health Explorer")
with img_col:
    # Hero image — photo by Marek Piwnicki on Unsplash (free to use under the
    # Unsplash License; photographer retains copyright, attribution not required
    # but included here as good practice).
    # Source: https://unsplash.com/photos/WiZOyYqzUss
    st.image(
        "assets/hero.jpg",
        caption="Photo by Marek Piwnicki / Unsplash",
        width=550,
    )

st.write(
    "This dashboard explores how socioeconomic conditions, air quality, greenhouse gas "
    "emissions, and health outcomes relate to one another across U.S. counties, using "
    "2023 data merged from four public sources."
)

col1, col2, col3 = st.columns(3)
col1.metric("Counties in dataset", f"{len(df):,}")
col2.metric("States represented", 52)
col3.metric("Data categories", len(VARIABLE_GROUPS))

st.markdown("---")
st.markdown("### How this dashboard is organized")
st.write(
    "Use the navigation sidebar on the left to move between topic pages. Each page focuses "
    "on one topic and is built around interactive charts. Hover for details and use the sidebar "
    "controls on each page to change what's shown. "
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### Emissions")
    st.write(
        "Greenhouse gas emissions by county — total emissions, per-capita emissions, "
        "gas type breakdown, and which states report the most."
    )
with c2:
    st.markdown("#### Socioeconomic")
    st.write(
        "Socioeconomic hardship indicators — food and housing insecurity, insurance "
        "access, and data coverage across states."
    )
with c3:
    st.markdown("#### Health & Pollution")
    st.write(
        "Health outcome prevalence — respiratory and mental health conditions — and how "
        "they relate to air pollution exposure."
    )

st.markdown("---")
st.markdown("### About the data")
st.write(
    "**Sources:** EPA Greenhouse Gas Reporting Program (2023), EPA Air Quality Index by "
    "CBSA (2023), CDC PLACES County Data (2025 release), and Census core-based statistical "
    "area definitions — merged to the county level.\n\n"
    "**Note on missing data:** air quality monitoring only covers roughly 1300 counties, "
    "and GHG emissions reporting is sparser in rural counties. Variable pairs that mix "
    "categories can end up with a smaller sample than a single-category view — each page "
    "shows how many counties are currently plotted.\n\n"
    "**Image credit:** Photo by Marek Piwnicki on Unsplash. "
    "https://unsplash.com/photos/WiZOyYqzUss"
)
