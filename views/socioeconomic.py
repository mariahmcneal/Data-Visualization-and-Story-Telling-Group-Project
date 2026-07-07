import altair as alt
import pandas as pd
import streamlit as st

from data_utils import (
    load_data,
    SES_VARS,
    VARIABLE_GROUPS,
    linked_scatter_bar,
    state_filter,
    COLOR_BAR,
)

@st.cache_data
def load_data():
    df = pd.read_csv("eda_env_health_2023.csv")
    return df
    
df = load_data()

st.title("🏘️ Environmental Burden and Socioeconomic Status (SES)")
st.caption("Owner: Michelle Webber")

st.markdown(
    """
    Environmental burdens are not experienced equally across communities. This dashboard explores environmental justice patterns across U.S. counties by examining how **socioeconomic conditions**, **air quality**, and **greenhouse gas emissions** vary geographically. Interactive visualizations highlight where environmental exposures and social vulnerabilities overlap, providing insight into communities that may face disproportionate environmental challenges.
    """
)


# -----------------------------
# Sidebar dropdowns
# -----------------------------

SES_labels = {
    "FOODINSECU_z": "Food Insecurity",
    "HOUSINSECU_z": "Housing Insecurity",
    "FOODSTAMP_z": "Food Assistance Reliance",
    "ACCESS2_z": "Healthcare Access Barriers",
    "SHUTUTILITY_z": "Utility Shutoff Risk",
    "LACKTRPT_z": "Transportation Barriers",
    "EMOTIONSPT_z": "Emotional Support Barriers"
}

ENV_labels = {
    "total_emissions_z": "Total Emissions",
    "co2_emissions_z": "CO₂ Emissions",
    "ch4_emissions_z": "CH₄ Emissions",
    "n2o_emissions_z": "N₂O Emissions",
    "emissions_per_capita_z": "Emissions per Capita",
    "Unhealthy Days_z": "Unhealthy Air Days"
}


with st.sidebar:
    st.header("Map Controls")

    selected_ses = st.selectbox(
        "Select SES Measure",
        options=list(SES_labels.keys()),
        format_func=lambda x: SES_labels[x],
        index=list(SES_labels.keys()).index("HOUSINSECU_z")
    )

    selected_env = st.selectbox(
        "Select Environmental Measure",
        options=list(ENV_labels.keys()),
        format_func=lambda x: ENV_labels[x],
        index=0
    )
  # -----------------------------
# SES MAP
# -----------------------------

ses_map = (
    alt.Chart(counties)
    .mark_geoshape(
        stroke="white",
        strokeWidth=0.1
    )

    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            df,
            "county_fips_int",
            [
                "county_name",
                "state_abbr",
                selected_ses,
                "FOODINSECU",
                "HOUSINSECU"
            ]
        )
    )

    .transform_calculate(
        SES_value=f"datum['{selected_ses}']"
    )

    .encode(

        color=alt.Color(
            "SES_value:Q",
            title="SES z-score",
            scale=alt.Scale(
                scheme="redyellowgreen",
                domain=[-2,2],
                reverse=True
            )
        ),

        tooltip=[
            alt.Tooltip("county_name:N", title="County"),
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(
                "SES_value:Q",
                title="SES z-score",
                format=".2f"
            ),
            alt.Tooltip(
                "HOUSINSECU:Q",
                title="Housing insecurity (%)",
                format=".1f"
            ),
            alt.Tooltip(
                "FOODINSECU:Q",
                title="Food insecurity (%)",
                format=".1f"
            )
        ]
    )

    .properties(
        width=450,
        height=500,
        title=f"Socioeconomic Vulnerability: {SES_labels[selected_ses]}"
    )

    .project(type="albersUsa")
)
env_map = (
    alt.Chart(counties)
    .mark_geoshape(
        stroke="white",
        strokeWidth=0.1
    )

    .transform_lookup(
        lookup="id",
        from_=alt.LookupData(
            df,
            "county_fips_int",
            [
                "county_name",
                "state_abbr",
                selected_env,
                "pct_unhealthy_days",
                "num_facilities"
            ]
        )
    )

    .transform_calculate(
        ENV_value=f"datum['{selected_env}']"
    )

    .encode(

        color=alt.Color(
            "ENV_value:Q",
            title="Environmental z-score",
            scale=alt.Scale(
                scheme="redyellowgreen",
                domain=[-2,2],
                reverse=True
            )
        ),

        tooltip=[
            alt.Tooltip("county_name:N", title="County"),
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(
                "ENV_value:Q",
                title="Environmental z-score",
                format=".2f"
            ),
            alt.Tooltip(
                "num_facilities:Q",
                title="Facilities",
                format=".0f"
            )
        ]
    )

    .properties(
        width=450,
        height=500,
        title=f"Environmental Burden: {ENV_labels[selected_env]}"
    )

    .project(type="albersUsa")
)
st.altair_chart(
    env_map | ses_map,
    use_container_width=True
)