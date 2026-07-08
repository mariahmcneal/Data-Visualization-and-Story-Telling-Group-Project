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
st.markdown("**Are regions with higher socioeconomic disadvantage also associated with higher concentrations of air pollutants that pose risks to human health?**")

st.markdown(
    """
    Environmental burdens are not experienced equally across the United States. This page explores how socioeconomic disadvantage overlaps with air pollution and greenhouse gas emissions across U.S. counties, highlighting where environmental exposures and social vulnerabilities are concentrated.
    """
)

st.divider()

# -----------------------------
# Sidebar dropdowns
# -----------------------------

SES_labels = {
    "HOUSINSECU_z": "Housing Insecurity",
    "FOODINSECU_z": "Food Insecurity",
    "FOODSTAMP_z": "Food Assistance Reliance",
    "ACCESS2_z": "Healthcare Access Barriers",
    "SHUTUTILITY_z": "Utility Shutoff Risk",
    "LACKTRPT_z": "Transportation Barriers",
    "EMOTIONSPT_z": "Emotional Support Barriers"
}


ENV_labels = {
    "num_facilities_z": "Number of Emitting Facilities",
    "emissions_per_capita_z": "Emissions per Capita",
    "pct_unhealthy_days_z": "% Unhealthy Air Quality Days",
    "Max AQI_z": "Maximum AQI",
    "90th Percentile AQI_z": "High AQI (90th Percentile)",
    "Median AQI_z": "Median AQI",
    "total_emissions_z": "Total Emissions",
    "co2_emissions_z": "CO₂ Emissions",
    "ch4_emissions_z": "Methane Emissions",
    "n2o_emissions_z": "Nitrous Oxide Emissions"
}

county_selection = alt.selection_point(
    fields=["id"],
    empty=True
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
        index=states.index("LA") if "LA" in states else 0
    )

    county_options = (
        df[df["state_abbr"] == selected_state]
        .sort_values("county_name")
    )

    selected_county = st.selectbox(
        "Select County:",
        options=county_options["county_display"],
        index=(
            list(county_options["county_display"]).index("East Carroll County, LA")
            if "East Carroll County, LA" in list(county_options["county_display"])
            else 0
        )
    )  
st.markdown(f"### Socioeconomic Vulnerability: {SES_labels[selected_ses]}")

 # Summary metrics for selected SES measure
ses_data = df[selected_ses].dropna()

avg_ses = df[selected_ses.replace("_z", "")].mean()

highest_county = (
    df.dropna(subset=[selected_ses])
    .sort_values(selected_ses, ascending=False)
    .iloc[0]
)

lowest_county = (
    df.dropna(subset=[selected_ses])
    .sort_values(selected_ses, ascending=True)
    .iloc[0]
)

m1, m2, m3 = st.columns(3)

m1.metric(
    "Average score",
    f"{avg_ses:.1f}%"
)

m2.metric(
    "Highest vulnerability county",
    f"{highest_county['county_name']}, {highest_county['state_abbr']}",
    f"{highest_county[selected_ses]:.2f} z-score"
)

m3.metric(
    "Counties analyzed",
    f"{ses_data.count():,}"
)
   
      
# -----------------------------
# SES MAP
# -----------------------------
selected_row = df[
    df["county_display"] == selected_county
].iloc[0]


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
                "HOUSINSECU"
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
        width=700,
        height=460
    )

    .project(type="albersUsa")
)


# -----------------------------
# Display maps + explanation
# -----------------------------

col1, col2 = st.columns([2, 1])

with col1:
    map_event = st.altair_chart(
        ses_map,
        use_container_width=True,
        on_select="rerun"
    )

with col2:
    st.info(
        """
        **How to read this map**

        Values are Z-scores, which standardize measures so counties can be 
        compared on the same scale.

        - **0** = national average  
        - **Positive values** = higher-than-average vulnerability  
        - **Negative values** = lower-than-average vulnerability  

        Higher values indicate counties with greater levels of the 
        selected measure.
        """
    )




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

value = selected_row[selected_env]

col3.metric(
    f"{ENV_labels[selected_env]} (z-score)",
    "Not reported" if pd.isna(value) else f"{value:.2f}"
)


