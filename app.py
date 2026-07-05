"""
Environmental & Community Health Explorer
-------------------------------------------
Streamlit + Altair dashboard skeleton for the Data Viz group project.

Data: merged_env_health_2023.csv (county-level GHG emissions, air quality (AQI),
socioeconomic indicators (SES), and PLACES health outcomes).

Run locally with:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Environmental & Community Health Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Data loading + cleaning (cached so it only runs once per session)
# ----------------------------------------------------------------------------
DATA_PATH = "merged_env_health_2023.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # TotalPopulation arrives as a comma-formatted string ("24,434")
    df["TotalPopulation"] = pd.to_numeric(
        df["TotalPopulation"].astype(str).str.replace(",", ""), errors="coerce"
    )

    # Make sure numeric columns are actually numeric
    numeric_cols = [
        "total_emissions", "co2_emissions", "ch4_emissions", "n2o_emissions",
        "num_facilities", "Median AQI", "Max AQI", "90th Percentile AQI",
        "Days with AQI", "Good Days", "Moderate Days", "Unhealthy Days",
        "Very Unhealthy Days", "Hazardous Days",
        "Unhealthy for Sensitive Groups Days",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived variables (same logic as the EDA notebook)
    df["emissions_per_capita"] = df["total_emissions"] / df["TotalPopulation"]
    df["log_total_emissions"] = np.log1p(df["total_emissions"])
    df["log_emissions_per_capita"] = np.log1p(df["emissions_per_capita"])

    return df


df = load_data(DATA_PATH)

# ----------------------------------------------------------------------------
# Variable groups (mirrors SES / AQI / EMISSIONS / HEALTH groups from the EDA notebook)
# Friendly label -> column name
# ----------------------------------------------------------------------------
VARIABLE_GROUPS = {
    "Socioeconomic (SES)": {
        "Food insecurity (%)": "FOODINSECU",
        "Housing insecurity (%)": "HOUSINSECU",
        "Food stamp / SNAP use (%)": "FOODSTAMP",
        "Lack of health insurance (%)": "ACCESS2",
        "Utility shutoff threat (%)": "SHUTUTILITY",
        "Lack of transportation (%)": "LACKTRPT",
        "Lack of social/emotional support (%)": "EMOTIONSPT",
    },
    "Air Quality (AQI)": {
        "Median AQI": "Median AQI",
        "Max AQI": "Max AQI",
        "90th percentile AQI": "90th Percentile AQI",
        "Days with AQI reported": "Days with AQI",
        "Good air quality days": "Good Days",
        "Moderate air quality days": "Moderate Days",
        "Unhealthy days": "Unhealthy Days",
        "Very unhealthy days": "Very Unhealthy Days",
        "Hazardous days": "Hazardous Days",
        "PM2.5 days": "Days PM2.5",
        "PM10 days": "Days PM10",
        "Ozone days": "Days Ozone",
    },
    "GHG Emissions": {
        "Total emissions (log)": "log_total_emissions",
        "Emissions per capita (log)": "log_emissions_per_capita",
        "Total emissions (raw)": "total_emissions",
        "CO2 emissions": "co2_emissions",
        "CH4 emissions": "ch4_emissions",
        "N2O emissions": "n2o_emissions",
        "Number of reporting facilities": "num_facilities",
    },
    "Health Outcomes (PLACES)": {
        "Mental health, not good days (%)": "MHLTH",
        "Physical health, not good days (%)": "PHLTH",
        "General health, fair/poor (%)": "GHLTH",
        "Asthma (%)": "CASTHMA",
        "COPD (%)": "COPD",
        "Coronary heart disease (%)": "CHD",
        "Stroke (%)": "STROKE",
        "Diabetes (%)": "DIABETES",
        "Obesity (%)": "OBESITY",
        "High blood pressure (%)": "BPHIGH",
        "High cholesterol (%)": "HIGHCHOL",
        "Depression (%)": "DEPRESSION",
        "Current smoking (%)": "CSMOKING",
        "Lack of physical activity (%)": "LPA",
        "Cognitive decline (%)": "COGNITION",
    },
}

ALL_LABELS = {label: col for group in VARIABLE_GROUPS.values() for label, col in group.items()}

# ----------------------------------------------------------------------------
# Sidebar — UI interactions (dropdowns + multiselect filter)
# ----------------------------------------------------------------------------
st.sidebar.header("Explore the Data")
st.sidebar.caption("Pick any two variables to compare across US counties.")

x_group = st.sidebar.selectbox("X-axis category", list(VARIABLE_GROUPS.keys()), index=2)
x_label = st.sidebar.selectbox("X-axis variable", list(VARIABLE_GROUPS[x_group].keys()))

y_group = st.sidebar.selectbox("Y-axis category", list(VARIABLE_GROUPS.keys()), index=3)
y_label = st.sidebar.selectbox("Y-axis variable", list(VARIABLE_GROUPS[y_group].keys()))

x_col = VARIABLE_GROUPS[x_group][x_label]
y_col = VARIABLE_GROUPS[y_group][y_label]

state_options = sorted(df["state_abbr"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect(
    "Filter by state (optional)", state_options, default=[]
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Tip:** drag a box on the scatter plot to brush-select counties — "
    "the bar chart on the right updates to show only the selected counties."
)

# ----------------------------------------------------------------------------
# Filter + prep the plotting data
# ----------------------------------------------------------------------------
plot_df = df.dropna(subset=[x_col, y_col, "state_abbr"]).copy()
if selected_states:
    plot_df = plot_df[plot_df["state_abbr"].isin(selected_states)]

# ----------------------------------------------------------------------------
# Main layout
# ----------------------------------------------------------------------------
st.title("🌎 Environmental & Community Health Explorer")
st.write(
    "Explore how socioeconomic conditions, air quality, greenhouse gas emissions, "
    "and health outcomes relate to one another across U.S. counties (2023 data)."
)

col_metric1, col_metric2, col_metric3 = st.columns(3)
col_metric1.metric("Counties shown", f"{len(plot_df):,}")
col_metric2.metric("States represented", plot_df["state_abbr"].nunique())
if len(plot_df) > 2:
    corr = plot_df[x_col].corr(plot_df[y_col])
    col_metric3.metric("Correlation (r)", f"{corr:.2f}")

st.markdown("### Coordinated view: scatter (brush to select) + state comparison")

# Within-visualization interaction: interval brush selection
brush = alt.selection_interval(encodings=["x", "y"])

scatter = (
    alt.Chart(plot_df)
    .mark_circle(size=65, opacity=0.65)
    .encode(
        x=alt.X(f"{x_col}:Q", title=x_label, scale=alt.Scale(zero=False)),
        y=alt.Y(f"{y_col}:Q", title=y_label, scale=alt.Scale(zero=False)),
        color=alt.condition(brush, alt.value("#1C7293"), alt.value("#D9D9D9")),
        tooltip=[
            alt.Tooltip("county_name:N", title="County"),
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(f"{x_col}:Q", title=x_label, format=".2f"),
            alt.Tooltip(f"{y_col}:Q", title=y_label, format=".2f"),
        ],
    )
    .add_params(brush)
    .properties(width=430, height=430, title=f"{x_label} vs. {y_label} (by county)")
)

bar = (
    alt.Chart(plot_df)
    .mark_bar(color="#065A82")
    .encode(
        y=alt.Y("state_abbr:N", sort="-x", title="State"),
        x=alt.X(f"mean({y_col}):Q", title=f"Mean {y_label}"),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(f"mean({y_col}):Q", title=f"Mean {y_label}", format=".2f"),
            alt.Tooltip("count():Q", title="Counties in selection"),
        ],
    )
    .transform_filter(brush)
    .properties(width=330, height=430, title="Mean of Y variable, brushed counties only")
)

combined = alt.hconcat(scatter, bar).resolve_scale(color="independent")
st.altair_chart(combined, use_container_width=False)

st.caption(
    "Drag a rectangle on the scatter plot to brush-select a group of counties. "
    "The bar chart recalculates the mean of the Y variable per state using only the "
    "selected points — this is the coordinated, linked-brushing interaction."
)

# ----------------------------------------------------------------------------
# Secondary view: distribution of the Y variable
# ----------------------------------------------------------------------------
st.markdown("### Distribution of the selected Y variable")

hist = (
    alt.Chart(plot_df)
    .mark_bar(color="#02C39A")
    .encode(
        x=alt.X(f"{y_col}:Q", bin=alt.Bin(maxbins=30), title=y_label),
        y=alt.Y("count():Q", title="Number of counties"),
        tooltip=[alt.Tooltip("count():Q", title="Counties")],
    )
    .properties(width=780, height=220)
)
st.altair_chart(hist, use_container_width=False)

with st.expander("View underlying data (filtered)"):
    st.dataframe(
        plot_df[["county_name", "state_abbr", x_col, y_col]].sort_values(y_col, ascending=False),
        use_container_width=True,
    )

st.markdown("---")
st.caption(
    "Data sources: EPA Greenhouse Gas Reporting Program (2023), EPA Air Quality Index "
    "by CBSA (2023), CDC PLACES County Data (2025 release), and Census core-based "
    "statistical area definitions."
)
