import altair as alt
import streamlit as st

from data_utils import (
    load_data,
    HEALTH_VARS,
    VARIABLE_GROUPS,
    linked_scatter_bar,
    state_filter,
    COLOR_ACCENT,
)

st.title("❤️ Health & Pollution")
st.caption("Owner: Dalis — based on the health outcome + pollution research questions from our EDA notebook")

df = load_data()

st.write(
    "Explore health outcome prevalence by county — respiratory conditions, mental health, "
    "and more — and how they relate to air pollution, emissions, or socioeconomic factors."
)

# --- Sidebar controls (UI interaction) ---------------------------------------
st.sidebar.header("Health view controls")

x_label = st.sidebar.selectbox("Health variable (X-axis)", list(HEALTH_VARS.keys()))
x_col = HEALTH_VARS[x_label]

other_groups = {k: v for k, v in VARIABLE_GROUPS.items() if k != "Health Outcomes (PLACES)"}
y_group = st.sidebar.selectbox(
    "Compare against category (Y-axis)", list(other_groups.keys()), index=1
)
y_label = st.sidebar.selectbox("Y-axis variable", list(other_groups[y_group].keys()))
y_col = other_groups[y_group][y_label]

selected_states = state_filter(st.sidebar, df, key="health_states")

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

# --- Topic-specific chart: distribution of the selected health outcome ---------
st.markdown("---")
st.markdown(f"### Distribution of {x_label} across counties")

hist = (
    alt.Chart(df.dropna(subset=[x_col]))
    .mark_bar(color=COLOR_ACCENT)
    .encode(
        x=alt.X(f"{x_col}:Q", bin=alt.Bin(maxbins=30), title=x_label),
        y=alt.Y("count():Q", title="Number of counties"),
        tooltip=[alt.Tooltip("count():Q", title="Counties")],
    )
    .properties(width=780, height=260)
)
st.altair_chart(hist, use_container_width=False)

with st.expander("View underlying data (filtered)"):
    st.dataframe(
        plot_df[["county_name", "state_abbr", x_col, y_col]].sort_values(x_col, ascending=False),
        use_container_width=True,
    )
