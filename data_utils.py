"""
Shared data loading + variable definitions for the multipage dashboard.
Every page imports from here so cleaning logic and variable groups stay in sync.
"""

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

DATA_PATH = "merged_env_health_2023.csv"


@st.cache_data
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    # TotalPopulation arrives as a comma-formatted string ("24,434")
    df["TotalPopulation"] = pd.to_numeric(
        df["TotalPopulation"].astype(str).str.replace(",", ""), errors="coerce"
    )

    numeric_cols = [
        "total_emissions", "co2_emissions", "ch4_emissions", "n2o_emissions",
        "num_facilities", "Median AQI", "Max AQI", "90th Percentile AQI",
        "Days with AQI", "Good Days", "Moderate Days", "Unhealthy Days",
        "Very Unhealthy Days", "Hazardous Days", "Unhealthy for Sensitive Groups Days",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["emissions_per_capita"] = df["total_emissions"] / df["TotalPopulation"]
    df["log_total_emissions"] = np.log1p(df["total_emissions"])
    df["log_emissions_per_capita"] = np.log1p(df["emissions_per_capita"])

    return df


# ----------------------------------------------------------------------------
# Variable groups — mirrors SES / AQI / EMISSIONS / HEALTH from the EDA notebook
# Friendly label -> column name
# ----------------------------------------------------------------------------
SES_VARS = {
    "Food insecurity (%)": "FOODINSECU",
    "Housing insecurity (%)": "HOUSINSECU",
    "Food stamp / SNAP use (%)": "FOODSTAMP",
    "Lack of health insurance (%)": "ACCESS2",
    "Utility shutoff threat (%)": "SHUTUTILITY",
    "Lack of transportation (%)": "LACKTRPT",
    "Lack of social/emotional support (%)": "EMOTIONSPT",
}

AQI_VARS = {
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
}

EMISSIONS_VARS = {
    "Total emissions (log)": "log_total_emissions",
    "Emissions per capita (log)": "log_emissions_per_capita",
    "Total emissions (raw)": "total_emissions",
    "CO2 emissions": "co2_emissions",
    "CH4 emissions": "ch4_emissions",
    "N2O emissions": "n2o_emissions",
    "Number of reporting facilities": "num_facilities",
}

HEALTH_VARS = {
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
}

VARIABLE_GROUPS = {
    "Socioeconomic (SES)": SES_VARS,
    "Air Quality (AQI)": AQI_VARS,
    "GHG Emissions": EMISSIONS_VARS,
    "Health Outcomes (PLACES)": HEALTH_VARS,
}

# Shared palette so every page looks consistent
COLOR_PRIMARY = "#1C7293"
COLOR_ACCENT = "#02C39A"
COLOR_MUTED = "#D9D9D9"
COLOR_BAR = "#065A82"


# ----------------------------------------------------------------------------
# Shared chart builder — used by every topic page so the interaction pattern
# (brush-select scatter -> linked state bar chart, with tooltips) stays identical.
# ----------------------------------------------------------------------------
def linked_scatter_bar(plot_df: pd.DataFrame, x_col: str, x_label: str, y_col: str, y_label: str):
    """Return an Altair hconcat: scatter (brushable) + bar chart of Y mean by state,
    filtered live by whatever is brushed on the scatter plot."""
    brush = alt.selection_interval(encodings=["x", "y"])

    scatter = (
        alt.Chart(plot_df)
        .mark_circle(size=65, opacity=0.65)
        .encode(
            x=alt.X(f"{x_col}:Q", title=x_label, scale=alt.Scale(zero=False)),
            y=alt.Y(f"{y_col}:Q", title=y_label, scale=alt.Scale(zero=False)),
            color=alt.condition(brush, alt.value(COLOR_PRIMARY), alt.value(COLOR_MUTED)),
            tooltip=[
                alt.Tooltip("county_name:N", title="County"),
                alt.Tooltip("state_abbr:N", title="State"),
                alt.Tooltip(f"{x_col}:Q", title=x_label, format=".2f"),
                alt.Tooltip(f"{y_col}:Q", title=y_label, format=".2f"),
            ],
        )
        .add_params(brush)
        .properties(width=430, height=420, title=f"{x_label} vs. {y_label} (by county)")
    )

    bar = (
        alt.Chart(plot_df)
        .mark_bar(color=COLOR_BAR)
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
        .properties(width=330, height=420, title="Mean by state (brushed counties only)")
    )

    return alt.hconcat(scatter, bar).resolve_scale(color="independent")


def variable_picker(sidebar, group_dict: dict, label: str, key: str, default_index: int = 0):
    """Render a single selectbox for one variable group and return (friendly_label, column_name)."""
    friendly = sidebar.selectbox(label, list(group_dict.keys()), index=default_index, key=key)
    return friendly, group_dict[friendly]


def state_filter(sidebar, df: pd.DataFrame, key: str):
    options = sorted(df["state_abbr"].dropna().unique().tolist())
    return sidebar.multiselect("Filter by state (optional)", options, default=[], key=key)
