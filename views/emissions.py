import altair as alt
import pandas as pd
import streamlit as st

from data_utils import (
    load_data,
    EMISSIONS_VARS,
    AQI_VARS,
    state_filter,
)

# ============================================================================
# Everything below is local to this page — nothing here touches data_utils.py.
# ============================================================================

# ----------------------------------------------------------------------------
# Page theme — warm oranges/reds, applied only while this page is active
# ----------------------------------------------------------------------------
FLAME_1 = "#FFC93C"   # warm yellow
FLAME_2 = "#FF7B54"   # orange
FLAME_3 = "#E63946"   # red
FLAME_4 = "#9D0208"   # deep red
MUTED = "#F2E2D2"

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFC93C22, #E6394622);
        border: 1px solid #E6394655;
        border-radius: 10px;
        padding: 10px 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Local helper: state FIPS codes, needed to join state-level data onto the
# US topojson map used by the choropleth below. Matches the numeric `id`
# field in the us-atlas topojson.
# ----------------------------------------------------------------------------
STATE_FIPS = {
    "AL": 1, "AK": 2, "AZ": 4, "AR": 5, "CA": 6, "CO": 8, "CT": 9, "DE": 10,
    "DC": 11, "FL": 12, "GA": 13, "HI": 15, "ID": 16, "IL": 17, "IN": 18,
    "IA": 19, "KS": 20, "KY": 21, "LA": 22, "ME": 23, "MD": 24, "MA": 25,
    "MI": 26, "MN": 27, "MS": 28, "MO": 29, "MT": 30, "NE": 31, "NV": 32,
    "NH": 33, "NJ": 34, "NM": 35, "NY": 36, "NC": 37, "ND": 38, "OH": 39,
    "OK": 40, "OR": 41, "PA": 42, "RI": 44, "SC": 45, "SD": 46, "TN": 47,
    "TX": 48, "UT": 49, "VT": 50, "VA": 51, "WA": 53, "WV": 54, "WI": 55,
    "WY": 56,
}

US_STATES_TOPOJSON_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"


def us_choropleth(state_df, value_col, value_label, color_scheme="oranges",
                   width=700, height=420, title=""):
    """Build a hoverable US state choropleth. Local to the emissions page.

    state_df must have a `state_abbr` column and the given value_col (one row per state).
    Uses the public us-atlas topojson, fetched client-side by the browser at render
    time — no server-side geo file needed.
    """
    state_df = state_df.copy()
    state_df["fips_id"] = state_df["state_abbr"].map(STATE_FIPS)
    state_df = state_df.dropna(subset=["fips_id"])

    states = alt.topo_feature(US_STATES_TOPOJSON_URL, "states")

    return (
        alt.Chart(states)
        .mark_geoshape(stroke="white", strokeWidth=0.6)
        .encode(
            color=alt.Color(
                f"{value_col}:Q", title=value_label, scale=alt.Scale(scheme=color_scheme)
            ),
            tooltip=[
                alt.Tooltip("state_abbr:N", title="State"),
                alt.Tooltip(f"{value_col}:Q", title=value_label, format=",.1f"),
            ],
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(state_df, "fips_id", [value_col, "state_abbr"]),
        )
        .project(type="albersUsa")
        .properties(width=width, height=height, title=title)
    )


def flame_linked_scatter_bar(plot_df, x_col, x_label, y_col, y_label):
    """Same brush-select scatter + linked state bar chart pattern as
    data_utils.linked_scatter_bar(), recolored for this page. Kept local so the
    shared version other pages use stays untouched."""
    brush = alt.selection_interval(encodings=["x", "y"])

    scatter = (
        alt.Chart(plot_df)
        .mark_circle(size=65, opacity=0.7)
        .encode(
            x=alt.X(f"{x_col}:Q", title=x_label, scale=alt.Scale(zero=False)),
            y=alt.Y(f"{y_col}:Q", title=y_label, scale=alt.Scale(zero=False)),
            color=alt.condition(brush, alt.value(FLAME_3), alt.value(MUTED)),
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
        .mark_bar(color=FLAME_2)
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


# ============================================================================
# Page content
# ============================================================================
df = load_data()

# ----------------------------------------------------------------------------
# 1. THE HOOK
# ----------------------------------------------------------------------------
st.title("Tracing GHGs to Air Quality")
st.markdown(
    "**Are regions with higher greenhouse gas emissions also associated with higher "
    "concentrations of air pollutants that pose risks to human health?**\n\n"
    "Every year, industrial facilities across the U.S. report their greenhouse gas "
    "emissions to the EPA. Some states carry a larger share of the load than "
    "others. This page explores where the emissions are concentrated, and whether "
    "counties with more emissions experience worse air quality."
)

total_all = df["total_emissions"].sum()
top_state_row = (
    df.dropna(subset=["total_emissions"])
    .groupby("state_abbr")["total_emissions"].sum()
    .sort_values(ascending=False)
    .head(1)
)
top_state_name = top_state_row.index[0]
top_state_share = top_state_row.iloc[0] / total_all * 100

m1, m2, m3 = st.columns(3)
m1.metric("Total reported emissions", f"{total_all/1e6:,.1f}M metric tons")
m2.metric("Top-emitting state", top_state_name, f"{top_state_share:.1f}% of the U.S. total")
m3.metric("Reporting facilities", f"{int(df['num_facilities'].sum(skipna=True)):,}")

# ----------------------------------------------------------------------------
# 2. THE MAP — where is it concentrated?
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🗺️ Where the emissions are")
st.write(
    "Hover over any state to see its total reported emissions. A handful of "
    "industrial and energy-producing states account for a disproportionate share."
)

state_emissions = (
    df.dropna(subset=["total_emissions"])
    .groupby("state_abbr", as_index=False)["total_emissions"]
    .sum()
)

st.altair_chart(
    us_choropleth(
        state_emissions,
        value_col="total_emissions",
        value_label="Total Emissions",
        color_scheme="oranges",
        width=780,
        height=460,
        title="Total GHG Emissions by State (all reporting counties)",
    ),
    use_container_width=False,
)

# ----------------------------------------------------------------------------
# 3. THE ZOOM-IN — the core research question
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🔬 Are high-emissions counties also higher-pollution counties?")
st.write(
    "The map shows *where* the emissions are. Here we test the actual question: pick "
    "an emissions measure and an air quality measure, then **drag a box on the "
    "scatter plot** to select a cluster of counties and see how their air quality "
    "compares state by state."
)

st.sidebar.header("🔥 Emissions story controls")
x_label = st.sidebar.selectbox("Emissions variable (X-axis)", list(EMISSIONS_VARS.keys()))
x_col = EMISSIONS_VARS[x_label]

y_label = st.sidebar.selectbox("Air quality variable (Y-axis)", list(AQI_VARS.keys()))
y_col = AQI_VARS[y_label]

selected_states = state_filter(st.sidebar, df, key="emissions_states")

plot_df = df.dropna(subset=[x_col, y_col, "state_abbr"]).copy()
if selected_states:
    plot_df = plot_df[plot_df["state_abbr"].isin(selected_states)]

c1, c2 = st.columns(2)
c1.metric("Counties shown", f"{len(plot_df):,}")
if len(plot_df) > 2:
    c2.metric("Correlation (r)", f"{plot_df[x_col].corr(plot_df[y_col]):.2f}")

st.altair_chart(
    flame_linked_scatter_bar(plot_df, x_col, x_label, y_col, y_label),
    use_container_width=False,
)
st.caption(
    "Drag a rectangle on the scatter plot to brush-select a group of counties — the "
    "bar chart recalculates the state averages using only that selection. Note that "
    "AQI monitoring only covers roughly 500 U.S. counties, so this comparison uses a "
    "smaller sample than the map above."
)

# ----------------------------------------------------------------------------
# 4. SUPPORTING CONTEXT — who carries the biggest burden?
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### ⚖️ Context: total emissions vs. per-capita emissions")
st.write(
    "One reason emissions and air quality don't always line up perfectly: total "
    "emissions favor states with more industry and more people, while per-capita "
    "emissions surface a different set of states carrying an outsized burden "
    "relative to their population. Each bubble is a state; size and color both "
    "track per-capita emissions."
)

state_summary = (
    df.dropna(subset=["total_emissions", "TotalPopulation"])
    .groupby("state_abbr", as_index=False)
    .agg(total_emissions=("total_emissions", "sum"), population=("TotalPopulation", "sum"))
)
state_summary["per_capita"] = state_summary["total_emissions"] / state_summary["population"]

bubble = (
    alt.Chart(state_summary)
    .mark_circle(opacity=0.8)
    .encode(
        x=alt.X("total_emissions:Q", title="Total emissions", scale=alt.Scale(type="log")),
        y=alt.Y("per_capita:Q", title="Emissions per capita"),
        size=alt.Size("per_capita:Q", legend=None, scale=alt.Scale(range=[50, 1200])),
        color=alt.Color(
            "per_capita:Q",
            title="Per-capita emissions",
            scale=alt.Scale(scheme="redyellowblue", reverse=True),
        ),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip("total_emissions:Q", title="Total emissions", format=",.0f"),
            alt.Tooltip("per_capita:Q", title="Per-capita emissions", format=",.2f"),
        ],
    )
    .properties(width=780, height=420, title="Total vs. per-capita emissions, by state")
)
st.altair_chart(bubble, use_container_width=False)

# ----------------------------------------------------------------------------
# 5. THE TAKEAWAY
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, {FLAME_1}22, {FLAME_3}22);
                border-left: 5px solid {FLAME_3}; border-radius: 6px; padding: 14px 18px;">
    <strong>Takeaway:</strong> Emissions are concentrated in a small number of states,
    but whether that concentration translates into worse air quality on the ground is
    a county-level question, not a state-level one — use the scatter plot above to
    check the correlation for the emissions and air quality measures you care about,
    and brush-select any cluster of counties to see how their air quality compares.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("View underlying data (filtered)"):
    st.dataframe(
        plot_df[["county_name", "state_abbr", x_col, y_col]].sort_values(x_col, ascending=False),
        use_container_width=True,
    )
