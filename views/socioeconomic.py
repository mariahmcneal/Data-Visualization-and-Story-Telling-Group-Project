import altair as alt
import pandas as pd
import streamlit as st

from data_utils import (
    SES_VARS,
    VARIABLE_GROUPS,
    linked_scatter_bar,
    state_filter,
    COLOR_BAR,
)

US_COUNTIES_TOPOJSON_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json"

@st.cache_data
def load_socioeconomic_data():
    df = pd.read_csv("eda_env_health_2023.csv")
    return df

df = load_socioeconomic_data()

df = df.sort_values(["state_abbr", "county_name"])

df["county_display"] = (
    df["county_name"] + " County, " + df["state_abbr"]
)

df["county_fips_int"] = (
    df["county_fips_int"]
    .astype(str)
    .str.zfill(5)
)

@st.cache_data
def load_county_map():
    return alt.topo_feature(
        US_COUNTIES_TOPOJSON_URL,
        "counties"
    )

counties = load_county_map()
st.title("🏘️ Environmental Burden and Socioeconomic Status (SES)")
st.caption("Owner: Michelle Webber")

st.markdown(
    """
    Environmental burdens are not experienced equally across communities. This dashboard explores environmental justice patterns across U.S. counties by examining how **socioeconomic conditions**, **air quality**, and **greenhouse gas emissions** vary geographically. Interactive visualizations highlight where environmental exposures and social vulnerabilities overlap, providing insight into communities that may face disproportionate environmental challenges.
    """
)

st.info(
    """
    **Note:** Values are Z-scores which standardize measures so counties can 
    be compared on the same scale. A z-score of 0 represents the national average. 
    Positive values indicate counties with higher-than-average values for the 
    selected measure, while negative values indicate lower-than-average values.
    
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
    "pct_unhealthy_days_z": "% Unhealthy Air Quality Days",
    "Max AQI_z": "Maximum AQI",
    "90th Percentile AQI_z": "High AQI (90th Percentile)",
    "Median AQI_z": "Median AQI",
    "total_emissions_z": "Total Emissions",
    "co2_emissions_z": "CO₂ Emissions",
    "ch4_emissions_z": "Methane Emissions",
    "n2o_emissions_z": "Nitrous Oxide Emissions",
    "num_facilities_z": "Number of Emitting Facilities",
    "emissions_per_capita_z": "Emissions per Capita"
}

county_selection = alt.selection_point(
    fields=["county_fips_int"],
    empty=False
)

with st.sidebar:
    st.header("Explore Variables")

    selected_ses = st.selectbox(
        "Select SES Measure:",
        options=list(SES_labels.keys()),
        format_func=lambda x: SES_labels[x],
        index=list(SES_labels.keys()).index("HOUSINSECU_z")
    )

    selected_env = st.selectbox(
        "Select Environmental Measure:",
        options=list(ENV_labels.keys()),
        format_func=lambda x: ENV_labels[x],
        index=0
    )

    states = sorted(df["state_abbr"].unique())

    selected_state = st.selectbox(
        "Select State",
        options=states,
        index=states.index("MA") if "MA" in states else 0
    )

    county_options = (
        df[df["state_abbr"] == selected_state]
        .sort_values("county_name")
    )

    selected_county = st.selectbox(
        "Select County:",
        options=county_options["county_display"],
        index=(
            list(county_options["county_display"]).index("Suffolk County, MA")
            if "Suffolk County, MA" in list(county_options["county_display"])
            else 0
        )
    )  
    burden_threshold = st.slider(
        "Highlight counties with SES Indicator z-score above:",
        min_value=-2.0,
        max_value=3.0,
        value=1.0,
        step=0.1
    )
      
# -----------------------------
# SES MAP
# -----------------------------
selected_row = df[
    df["county_display"] == selected_county
].iloc[0]

df["highlight"] = (
    (df[selected_ses] >= burden_threshold) &
    (df[selected_env] >= burden_threshold)
)

highlighted_counties = df[df["highlight"]]

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
                "county_fips_int",
                "county_name",
                "state_abbr",
                selected_ses,
                "FOODINSECU",
                "HOUSINSECU",
                "highlight"
            ]
        )
    )

    .transform_calculate(
        SES_value=f"datum['{selected_ses}']"
    )

    .add_params(county_selection)

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
        
        stroke=alt.condition(
            "datum.highlight == true",
            alt.value("black"),
            alt.value("white")
        ),
        
        strokeWidth=alt.condition(
            "datum.highlight == true",
            alt.value(1.5),
            alt.value(0.1)
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
                "county_fips_int",
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

    .add_params(county_selection)

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

st.divider()

st.subheader("Selected County Profile")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Selected County",
    selected_county
)

col2.metric(
    f"{SES_labels[selected_ses]} (z-score)",
    f"{selected_row[selected_ses]:.2f}"
)

col3.metric(
    f"{ENV_labels[selected_env]} (z-score)",
    f"{selected_row[selected_env]:.2f}"
)

# Display maps and capture selections
st.caption(
    "Map colors represent relative county values compared with all U.S. counties."
)

st.caption(
    f"{len(highlighted_counties)} counties have a "
    f"{SES_labels[selected_ses]} z-score above {burden_threshold:.1f}."
)

ses_event = st.altair_chart(
    ses_map,
    use_container_width=True,
    on_select="rerun"
)

env_event = st.altair_chart(
    env_map,
    use_container_width=True,
    on_select="rerun"
)
