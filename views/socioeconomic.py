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
    "Counties analyzed",
    f"{ses_data.count():,}"
)

df["num_facilities_z_display"] = df["num_facilities_z"].apply(
    lambda x: "Not reported" if pd.isna(x) or str(x).lower() == "nan" else f"{float(x):.1f}"
)

df["emissions_per_capita_z_display"] = df["emissions_per_capita_z"].apply(
    lambda x: "Not reported" if pd.isna(x) or str(x).lower() == "nan" else f"{float(x):.1f}"
)   
# -----------------------------
# SES MAP
# -----------------------------

df["county_fips_int"] = df["county_fips_int"].astype(str)

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
                "num_facilities_z_display",
                "emissions_per_capita_z_display"
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
            alt.Tooltip("county_fips_int:N", title="FIPS"),
            alt.Tooltip(
                "SES_value:Q",
                title="SES z-score",
                format=".1f"
            ),
            alt.Tooltip(
                "num_facilities_z_display:N",
                title="Number of facilities z-score"
            ),
            alt.Tooltip(
                "emissions_per_capita_z_display:N",
                title="Emissions per capita z-score"
            )
        ]
    )


    .properties(
        width=700,
        height=460
    )

    .project(type="albersUsa")
)



scatter_df = df[
    [
        "county_fips_int",
        "county_name",
        "state_abbr",
        selected_ses,
        selected_env,
        "num_facilities"
    ]
].dropna().copy()

click = alt.selection_point(
    fields=["county_name"],
    empty=True
)

hotspot_chart = (
    alt.Chart(scatter_df)
    .mark_circle(size=80)
    .encode(
        color=alt.condition(
            click,
            alt.value("maroon"),
            alt.value("lightgray")
        ),
        
        x=alt.X(
            f"{selected_env}:Q",
            title=f"{ENV_labels.get(selected_env, selected_env)} (z-score)"
        ),
        y=alt.Y(
            f"{selected_ses}:Q",
            title=f"{SES_labels.get(selected_ses, selected_ses)} (z-score)"
        ),
        tooltip=[
            alt.Tooltip("county_name:N", title="County"),
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(
                f"{selected_ses}:Q",
                title=SES_labels.get(selected_ses, selected_ses),
                format=".2f"
            ),
            alt.Tooltip(
                f"{selected_env}:Q",
                title=ENV_labels.get(selected_env, selected_env),
                format=".2f"
            ),
            alt.Tooltip("num_facilities:Q", title="Facilities")
        ]
    )
    .properties(
        height=450,
        title="Counties with High Socioeconomic Vulnerability and Environmental Burden (Top-Right Quadrant)"
    )
)

x_rule = alt.Chart(
    pd.DataFrame({"x":[0]})
).mark_rule().encode(x="x")

y_rule = alt.Chart(
    pd.DataFrame({"y":[0]})
).mark_rule().encode(y="y")

hotspot_with_rules = hotspot_chart + x_rule + y_rule



# -----------------------------
# Display maps + explanation
# -----------------------------

col1, col2 = st.columns([2, 1])

with col1:
    st.altair_chart(
        ses_map,
        use_container_width=True
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


st.divider()


hotspots = scatter_df[
    (scatter_df[selected_ses] > 0) &
    (scatter_df[selected_env] > 0)
].copy()

hotspots["combined_score"] = (
    hotspots[selected_ses] +
    hotspots[selected_env]
)

hotspots = (
    hotspots
    .sort_values(
        "combined_score",
        ascending=False
    )
    .head(15)
)

hotspots["county_label"] = (
    hotspots["county_name"] + ", " + hotspots["state_abbr"]
)

hotspot_bar = (
    alt.Chart(hotspots)
    .mark_bar()
    .add_params(click)
    .encode(
        x=alt.X(
            "combined_score:Q",
            title= "Combined SES + Environmental Burden Score"
        ),
        y=alt.Y(
            "county_label:N",
            sort="-x",
            title="County"
        ),
        color=alt.condition(
            click,
            alt.value("maroon"),
            alt.value("lightgray")
        ),
        tooltip=[
            alt.Tooltip("county_name:N", title="County"),
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip(
                "combined_score:Q",
                title="Combined Score",
                format=".2f"
            ),
            alt.Tooltip(
                f"{selected_ses}:Q",
                title=SES_labels[selected_ses],
                format=".2f"
            ),
            alt.Tooltip(
                f"{selected_env}:Q",
                title=ENV_labels[selected_env],
                format=".2f"
            ),
            alt.Tooltip(
                "num_facilities:Q",
                title="Number of Facilities"
            )
        ]
    )
    .properties(
        height=350,
        title=[
            "Top 15 Environmental + Socioeconomic Hotspots",
            "Click on bars to highlight counties in the scatter plot"
        ]
    )  
)
dashboard = hotspot_with_rules & hotspot_bar
st.altair_chart(
    dashboard,
    use_container_width=True
)



st.divider()

st.subheader("Key Statistical Findings")

st.info(
"""
**Environmental Burden and Socioeconomic Vulnerability**

The number of industrial facilities showed the strongest statistically significant relationships 
with socioeconomic vulnerability measures (p-value < 0.01).

**Strongest correlations:**

• Lack of Emotional Support: r = 0.18  
• Loneliness: r = 0.14  
• Housing Insecurity: r = 0.10  
• Healthcare Access Barriers: r = 0.08  

These results indicate a **positive association**: counties with more facilities 
tended to have slightly higher levels of socioeconomic vulnerability.

Use the map and county selection tools to identify counties where high socioeconomic vulnerability overlaps with higher environmental burden.
"""
)

with st.expander("View underlying data (filtered)"):
    display_cols = [
        "county_name",
        "state_abbr",
        "county_fips_int",
    ] + list(SES_labels.keys()) + list(ENV_labels.keys())

    display_df = df[display_cols].rename(
        columns={**SES_labels, **ENV_labels}
    )

    st.dataframe(
        display_df.sort_values("county_name"),
        use_container_width=True,
    )