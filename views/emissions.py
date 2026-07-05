import altair as alt
import streamlit as st

from data_utils import (
    load_data,
    EMISSIONS_VARS,
    VARIABLE_GROUPS,
    linked_scatter_bar,
    state_filter,
    COLOR_BAR,
)

st.title("🏭 Emissions")
st.caption("Owner: Mariah — based on the emissions charts from our EDA notebook")

df = load_data()

st.write(
    "Explore greenhouse gas emissions by county, and how they relate to air quality, "
    "socioeconomic conditions, or health outcomes."
)

# --- Sidebar controls (UI interaction) ---------------------------------------
st.sidebar.header("Emissions view controls")

x_label = st.sidebar.selectbox("Emissions variable (X-axis)", list(EMISSIONS_VARS.keys()))
x_col = EMISSIONS_VARS[x_label]

other_groups = {k: v for k, v in VARIABLE_GROUPS.items() if k != "GHG Emissions"}
y_group = st.sidebar.selectbox("Compare against category (Y-axis)", list(other_groups.keys()))
y_label = st.sidebar.selectbox("Y-axis variable", list(other_groups[y_group].keys()))
y_col = other_groups[y_group][y_label]

selected_states = state_filter(st.sidebar, df, key="emissions_states")

# --- Filter data ---------------------------------------------------------------
plot_df = df.dropna(subset=[x_col, y_col, "state_abbr"]).copy()
if selected_states:
    plot_df = plot_df[plot_df["state_abbr"].isin(selected_states)]

m1, m2 = st.columns(2)
m1.metric("Counties shown", f"{len(plot_df):,}")
if len(plot_df) > 2:
    m2.metric("Correlation (r)", f"{plot_df[x_col].corr(plot_df[y_col]):.2f}")

st.markdown("### Coordinated view: brush-select counties, see the state comparison update")
st.altair_chart(
    linked_scatter_bar(plot_df, x_col, x_label, y_col, y_label),
    use_container_width=False,
)
st.caption(
    "Drag a rectangle on the scatter plot to select a group of counties — the bar chart "
    "recalculates using only that selection."
)

# --- Topic-specific chart: top states by total emissions (from the EDA notebook) ---
st.markdown("---")
st.markdown("### Top 15 states by total emissions")

state_emissions = (
    df.dropna(subset=["total_emissions"])
    .groupby("state_abbr", as_index=False)["total_emissions"]
    .sum()
    .sort_values("total_emissions", ascending=False)
    .head(15)
)

top_states_chart = (
    alt.Chart(state_emissions)
    .mark_bar(color=COLOR_BAR)
    .encode(
        x=alt.X("total_emissions:Q", title="Total emissions (all reporting counties)"),
        y=alt.Y("state_abbr:N", sort="-x", title="State"),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip("total_emissions:Q", title="Total emissions", format=",.0f"),
        ],
    )
    .properties(width=780, height=380)
)
st.altair_chart(top_states_chart, use_container_width=False)

with st.expander("View underlying data (filtered)"):
    st.dataframe(
        plot_df[["county_name", "state_abbr", x_col, y_col]].sort_values(x_col, ascending=False),
        use_container_width=True,
    )
