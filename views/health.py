# ── views/health.py ───────────────────────────────────────────────────────────
# Owner: Dalis
# Health and Pollution topic page for the Streamlit multipage dashboard
# Do not edit data_utils.py or any teammate file without group chat approval
# ─────────────────────────────────────────────────────────────────────────────

# Import libraries
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import pearsonr

from data_utils import COLOR_ACCENT, load_data, state_filter

# ── U.S. Census Bureau region lookup ──────────────────────────────────────────
# Territories (PR, GU, VI) are labeled in the map but excluded from dropdown options
CENSUS_REGION_MAP = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast",
    "NH": "Northeast", "RI": "Northeast", "VT": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",
    "IL": "Midwest",   "IN": "Midwest",   "MI": "Midwest",
    "OH": "Midwest",   "WI": "Midwest",   "IA": "Midwest",
    "KS": "Midwest",   "MN": "Midwest",   "MO": "Midwest",
    "NE": "Midwest",   "ND": "Midwest",   "SD": "Midwest",
    "DE": "South",     "FL": "South",     "GA": "South",
    "MD": "South",     "NC": "South",     "SC": "South",
    "VA": "South",     "DC": "South",     "WV": "South",
    "AL": "South",     "KY": "South",     "MS": "South",
    "TN": "South",     "AR": "South",     "LA": "South",
    "OK": "South",     "TX": "South",
    "AZ": "West",      "CO": "West",      "ID": "West",
    "MT": "West",      "NV": "West",      "NM": "West",
    "UT": "West",      "WY": "West",      "AK": "West",
    "CA": "West",      "HI": "West",      "OR": "West",
    "WA": "West",
    "PR": "Territories", "GU": "Territories", "VI": "Territories",
    "AS": "Territories", "MP": "Territories",
}

# ── Helper: OLS trend line DataFrame ──────────────────────────────────────────
def ols_line_df(df_src, x_col, y_col, n_points=120):
    # Compute an OLS regression line in pandas to avoid Vega-Lite JS errors
    clean = df_src[[x_col, y_col]].dropna()
    if len(clean) < 3:
        return pd.DataFrame({x_col: [], y_col: []})
    slope, intercept = np.polyfit(clean[x_col], clean[y_col], 1)
    x_vals = np.linspace(clean[x_col].min(), clean[x_col].max(), n_points)
    return pd.DataFrame({x_col: x_vals, y_col: np.polyval([slope, intercept], x_vals)})


# ── Helper: emission scatter and OLS trend line ────────────────────────────────
def emission_scatter_chart(df_src, y_col, y_label, dot_color, title, subtitle):
    # Drop rows missing either variable
    src   = df_src.dropna(subset=["log_emissions_per_capita", y_col]).copy()
    n_src = len(src)
    trend_data = ols_line_df(src, "log_emissions_per_capita", y_col)

    # Scatter layer
    pts = (
        alt.Chart(src)
        .mark_circle(size=40, opacity=0.45, color=dot_color)
        .encode(
            x=alt.X("log_emissions_per_capita:Q", title="Log Emissions Per Capita"),
            y=alt.Y(f"{y_col}:Q",                 title=f"{y_label} (%)"),
            tooltip=[
                alt.Tooltip("county_name:N",              title="County"),
                alt.Tooltip("state_abbr:N",               title="State"),
                alt.Tooltip("census_region:N",            title="Region"),
                alt.Tooltip("log_emissions_per_capita:Q", title="Log Emissions PC", format=".2f"),
                alt.Tooltip(f"{y_col}:Q",                 title=y_label, format=".1f"),
            ]
        )
    )

    # OLS trend line from the pandas-computed DataFrame
    tline = (
        alt.Chart(trend_data)
        .mark_line(color="darkred", strokeDash=[6, 3], strokeWidth=2)
        .encode(
            x=alt.X("log_emissions_per_capita:Q"),
            y=alt.Y(f"{y_col}:Q")
        )
    )

    return (pts + tline).properties(
        width=360, height=300,
        title=alt.TitleParams(title, subtitle=[f"{subtitle}  |  n = {n_src:,} counties"])
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Health Outcomes & Industrial Emission Burden")
st.caption(
    "Exploring how per-capita industrial greenhouse gas emissions relate to "
    "respiratory, cardiovascular, and neurological health outcomes across U.S. counties."
)

# Load the shared dataset
df = load_data()

# Create log_emissions_per_capita if not already present from load_data
if "log_emissions_per_capita" not in df.columns:
    df["TotalPopulation"] = pd.to_numeric(
        df["TotalPopulation"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df["emissions_per_capita"]     = df["total_emissions"] / df["TotalPopulation"]
    df["log_emissions_per_capita"] = np.log1p(df["emissions_per_capita"])

# Assign census region using the state abbreviation lookup
df["census_region"] = df["state_abbr"].map(CENSUS_REGION_MAP).fillna("Territories")

# ── Outcome variable options ───────────────────────────────────────────────────
OUTCOME_MAP = {
    "COPD":                       "COPD",
    "Coronary Heart Disease":     "CHD",
    "Current Asthma":             "CASTHMA",
    "Hearing Disability":         "HEARING",
    "High Blood Pressure":        "BPHIGH",
    "Stroke":                     "STROKE",
    "Cognitive Disability":       "COGNITION",
    "Frequent Physical Distress": "PHLTH",
    "Depression":                 "DEPRESSION",
    "Frequent Mental Distress":   "MHLTH",
    "Diabetes":                   "DIABETES",
    "Any Disability":             "DISABILITY",
}

# ── Sidebar controls ──────────────────────────────────────────────────────────
st.sidebar.header("Health & Pollution Controls")

outcome_label = st.sidebar.selectbox(
    "Health Outcome (scatter)",
    list(OUTCOME_MAP.keys()),
    index=0,
)
outcome_col = OUTCOME_MAP[outcome_label]

# Territories excluded from region options because emissions data does not map there
REGION_OPTIONS = ["Northeast", "Midwest", "South", "West"]
selected_regions = st.sidebar.multiselect(
    "Filter by Census Region",
    options=REGION_OPTIONS,
    default=[],
    help="Leave empty to include all regions.",
)

selected_states = state_filter(st.sidebar, df, key="health_states")

# ── Apply filters ─────────────────────────────────────────────────────────────
df_plot = df.dropna(subset=["log_emissions_per_capita", outcome_col]).copy()

if selected_regions:
    df_plot = df_plot[df_plot["census_region"].isin(selected_regions)]

if selected_states:
    df_plot = df_plot[df_plot["state_abbr"].isin(selected_states)]

# ── County count display ──────────────────────────────────────────────────────
n_counties   = len(df_plot)
region_label = ", ".join(selected_regions) if selected_regions else "All Regions"

m1, m2, m3 = st.columns(3)
m1.metric("Counties in view", f"{n_counties:,}")
if n_counties > 2:
    r_val = df_plot["log_emissions_per_capita"].corr(df_plot[outcome_col])
    m2.metric("Pearson r", f"{r_val:.3f}")
    m3.metric("Mean prevalence", f"{df_plot[outcome_col].mean():.1f}%")

if n_counties < 100:
    st.warning(
        f"Only {n_counties:,} counties match the current filter. "
        "Correlation estimates may be unstable. "
        "Consider broadening the region or state selection."
    )

st.markdown(
    "Industrial emission intensity varies dramatically across U.S. counties. "
    "Use the sidebar to select an outcome and filter by Census region or state. "
    "Drag a rectangle on the scatter plot to update the state bar chart."
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Coordinated scatter and state bar
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Log Emissions Per Capita vs. {outcome_label}")
st.caption(
    f"Region: {region_label}  |  n = {n_counties:,} counties.  "
    "Draw a rectangle on the scatter to update the state bar chart."
)

brush    = alt.selection_interval(name="county_brush")
trend_df = ols_line_df(df_plot, "log_emissions_per_capita", outcome_col)

scatter = (
    alt.Chart(df_plot)
    .mark_circle(size=40, opacity=0.5)
    .encode(
        x=alt.X("log_emissions_per_capita:Q", title="Log Emissions Per Capita"),
        y=alt.Y(f"{outcome_col}:Q",           title=f"{outcome_label} (%)"),
        color=alt.condition(brush, alt.Color("state_abbr:N", legend=None), alt.value("lightgray")),
        tooltip=[
            alt.Tooltip("county_name:N",              title="County"),
            alt.Tooltip("state_abbr:N",               title="State"),
            alt.Tooltip("census_region:N",            title="Region"),
            alt.Tooltip("log_emissions_per_capita:Q", title="Log Emissions PC", format=".2f"),
            alt.Tooltip(f"{outcome_col}:Q",           title=f"{outcome_label} (%)", format=".1f"),
        ]
    )
    .properties(width=440, height=360)
    .add_params(brush)
)

trend_line = (
    alt.Chart(trend_df)
    .mark_line(color="darkred", strokeDash=[6, 3], strokeWidth=2)
    .encode(x=alt.X("log_emissions_per_capita:Q"), y=alt.Y(f"{outcome_col}:Q"))
)

state_bar = (
    alt.Chart(df_plot)
    .mark_bar(color=COLOR_ACCENT, opacity=0.85)
    .encode(
        x=alt.X("mean_val:Q", title=f"Mean {outcome_label} (%)"),
        y=alt.Y("state_abbr:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip("mean_val:Q",   title=f"Mean {outcome_label} (%)", format=".1f"),
        ]
    )
    .transform_filter(brush)
    .transform_aggregate(mean_val=f"mean({outcome_col})", groupby=["state_abbr"])
    .properties(width=300, height=360)
)

st.altair_chart(
    ((scatter + trend_line) | state_bar).configure_view(strokeWidth=0),
    use_container_width=False
)

with st.expander("View underlying data"):
    st.dataframe(
        df_plot[["county_name", "state_abbr", "census_region",
                 "log_emissions_per_capita", outcome_col]]
        .sort_values(outcome_col, ascending=False),
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Correlation bar chart (full national dataset, no region filter)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Which Outcomes Track With Industrial Emissions?")
st.caption(
    "Pearson r computed for each health outcome vs log emissions per capita "
    "across the full national dataset. Hover for sample size and significance."
)

corr_rows = []
for label, colname in OUTCOME_MAP.items():
    tmp = df[["log_emissions_per_capita", colname]].dropna()
    if len(tmp) > 2:
        r, p = pearsonr(tmp["log_emissions_per_capita"], tmp[colname])
        corr_rows.append({"label": label, "r": round(r, 3), "n": len(tmp),
                          "sig": "p < 0.05" if p < 0.05 else "n.s."})

corr_df  = pd.DataFrame(corr_rows).sort_values("r", ascending=True)

corr_bars = (
    alt.Chart(corr_df).mark_bar()
    .encode(
        x=alt.X("r:Q", title="Pearson r", scale=alt.Scale(domain=[-0.10, 0.35])),
        y=alt.Y("label:N", sort="-x", title=None),
        color=alt.Color("r:Q", scale=alt.Scale(scheme="redblue", domain=[-0.15, 0.30]), legend=None),
        tooltip=[alt.Tooltip("label:N", title="Outcome"), alt.Tooltip("r:Q", title="r", format=".3f"),
                 alt.Tooltip("n:Q", title="n"), alt.Tooltip("sig:N", title="Significance")]
    )
    .properties(width=560, height=320,
                title=alt.TitleParams("Health Outcome Correlations with Industrial Emission Intensity",
                                      subtitle=["Full national dataset  |  Hover for sample size"]))
)
zero_rule = alt.Chart(pd.DataFrame({"r": [0]})).mark_rule(color="black", strokeWidth=1.2).encode(x="r:Q")
st.altair_chart(corr_bars + zero_rule, use_container_width=False)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Respiratory contrast (COPD vs CASTHMA)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Respiratory Contrast: COPD vs. Current Asthma ({region_label})")
col_left, col_right = st.columns(2)

with col_left:
    st.altair_chart(
        emission_scatter_chart(df_plot, "COPD", "COPD Prevalence", "#2166ac",
                               "COPD vs. Log Emissions Per Capita",
                               "Acquired inhalation injury pathway")
        .configure_title(fontSize=12, anchor="start"), use_container_width=False)

with col_right:
    st.altair_chart(
        emission_scatter_chart(df_plot, "CASTHMA", "Asthma Prevalence", "#4dac26",
                               "Current Asthma vs. Log Emissions Per Capita",
                               "Primarily heritable / indoor allergen pathway")
        .configure_title(fontSize=12, anchor="start"), use_container_width=False)

st.info(
    "The flat asthma trend is a negative control. If emissions were confounded with all "
    "outcomes equally, asthma would follow the same pattern as COPD. The divergence "
    "supports a genuine inhalation exposure mechanism for COPD."
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Cognitive disability vs Depression
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"### Neurological and Mental Health Outcomes ({region_label})")
col_cog, col_dep = st.columns(2)

with col_cog:
    st.altair_chart(
        emission_scatter_chart(df_plot, "COGNITION", "Cognitive Disability", "#7b2d8b",
                               "Cognitive Disability vs. Log Emissions Per Capita",
                               "Neuroinflammatory pathway")
        .configure_title(fontSize=12, anchor="start"), use_container_width=False)

with col_dep:
    st.altair_chart(
        emission_scatter_chart(df_plot, "DEPRESSION", "Depression Prevalence", "#b35806",
                               "Depression vs. Log Emissions Per Capita",
                               "SES pathway dominant")
        .configure_title(fontSize=12, anchor="start"), use_container_width=False)

st.info(
    "Depression correlates far more strongly with food insecurity and housing instability "
    "than with industrial emissions. See the SES page for that analysis."
)
