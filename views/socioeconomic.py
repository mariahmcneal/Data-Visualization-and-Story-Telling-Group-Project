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

st.title("🏘️ Socioeconomic (SES)")
st.caption("Owner: Michelle — based on the SES / missingness analysis from our EDA notebook")

df = load_data()

st.write(
    "Explore socioeconomic hardship indicators by county — food and housing insecurity, "
    "insurance access, and more — and how they relate to air quality, emissions, or "
    "health outcomes."
)

# --- Sidebar controls (UI interaction) ---------------------------------------
st.sidebar.header("Socioeconomic view controls")

x_label = st.sidebar.selectbox("SES variable (X-axis)", list(SES_VARS.keys()))
x_col = SES_VARS[x_label]

other_groups = {k: v for k, v in VARIABLE_GROUPS.items() if k != "Socioeconomic (SES)"}
y_group = st.sidebar.selectbox("Compare against category (Y-axis)", list(other_groups.keys()))
y_label = st.sidebar.selectbox("Y-axis variable", list(other_groups[y_group].keys()))
y_col = other_groups[y_group][y_label]

selected_states = state_filter(st.sidebar, df, key="ses_states")

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

# --- Topic-specific chart: SES data coverage by state (from the EDA notebook) ---
st.markdown("---")
st.markdown("### SES data coverage by state")
st.caption(
    "Reflects how completely each state's counties report socioeconomic indicators — "
    "coverage varies systematically, so SES comparisons are conditional on reporting."
)

ses_cols = list(SES_VARS.values())
coverage = df.copy()
coverage["ses_pct_complete"] = coverage[ses_cols].notna().mean(axis=1) * 100
state_coverage = (
    coverage.groupby("state_abbr", as_index=False)["ses_pct_complete"]
    .mean()
    .sort_values("ses_pct_complete", ascending=False)
)

coverage_chart = (
    alt.Chart(state_coverage)
    .mark_bar(color=COLOR_BAR)
    .encode(
        x=alt.X("ses_pct_complete:Q", title="Avg. % SES fields complete"),
        y=alt.Y("state_abbr:N", sort="-x", title="State"),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip("ses_pct_complete:Q", title="% complete", format=".1f"),
        ],
    )
    .properties(width=780, height=780)
)
st.altair_chart(coverage_chart, use_container_width=False)

with st.expander("View underlying data (filtered)"):
    st.dataframe(
        plot_df[["county_name", "state_abbr", x_col, y_col]].sort_values(x_col, ascending=False),
        use_container_width=True,
    )
