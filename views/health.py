
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
 
# Import shared utilities (state_filter removed: not compatible with this page)
from data_utils import COLOR_ACCENT, load_data
 
# ── U.S. Census Bureau region lookup ──────────────────────────────────────────
# Territories (PR, GU, VI) labeled in the map but excluded from filter options
# because EPA GHGRP emissions data does not map to those counties
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
 
# Region options used by all inline selectboxes on this page
REGION_OPTIONS = ["All Regions", "Northeast", "Midwest", "South", "West"]
 
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
    src        = df_src.dropna(subset=["log_emissions_per_capita", y_col]).copy()
    n_src      = len(src)
    r_val      = src["log_emissions_per_capita"].corr(src[y_col]) if n_src > 2 else float("nan")
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
        width=580, height=460,
        title=alt.TitleParams(
            title,
            subtitle=[f"{subtitle}  |  r = {r_val:.2f}  |  n = {n_src:,} counties"]
        )
    )
 
 
# ── Helper: apply region selectbox filter to a DataFrame ──────────────────────
def apply_region_filter(df_src, region):
    # Return the full dataset when All Regions is selected
    if region == "All Regions":
        return df_src.copy()
    return df_src[df_src["census_region"] == region].copy()
 
 
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
    ## Fix TotalPopulation stored as a comma-formatted string
    df["TotalPopulation"] = pd.to_numeric(
        df["TotalPopulation"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df["emissions_per_capita"]     = df["total_emissions"] / df["TotalPopulation"]
    df["log_emissions_per_capita"] = np.log1p(df["emissions_per_capita"])
 
# Assign census region using the state abbreviation lookup
df["census_region"] = df["state_abbr"].map(CENSUS_REGION_MAP).fillna("Territories")
 
# Health outcome variable lookup
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
 
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Coordinated scatter and state bar
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Explore: Emission Intensity vs. Health Outcome")
st.caption(
    "Use the controls below to select a Census region and health outcome. "
    "Draw a rectangle on the scatter plot to update the state bar chart."
)
 
# Inline controls: region and outcome side by side
ctrl1_left, ctrl1_right = st.columns(2)
with ctrl1_left:
    sel_region_1 = st.selectbox(
        "Census Region",
        options=REGION_OPTIONS,
        index=0,
        key="region_s1"
    )
with ctrl1_right:
    sel_outcome_1 = st.selectbox(
        "Health Outcome",
        options=list(OUTCOME_MAP.keys()),
        index=0,
        key="outcome_s1"
    )
 
outcome_col_1 = OUTCOME_MAP[sel_outcome_1]
 
# Apply region filter for this section
df_s1 = apply_region_filter(df, sel_region_1)
df_s1 = df_s1.dropna(subset=["log_emissions_per_capita", outcome_col_1]).copy()
n_s1  = len(df_s1)
 
# County count metrics row
m1, m2, m3 = st.columns(3)
m1.metric("Counties in view", f"{n_s1:,}")
if n_s1 > 2:
    r_s1 = df_s1["log_emissions_per_capita"].corr(df_s1[outcome_col_1])
    m2.metric("Pearson r", f"{r_s1:.3f}")
    m3.metric("Mean prevalence", f"{df_s1[outcome_col_1].mean():.1f}%")
 
# Plain-language explainer for lay viewers, collapsed by default
with st.expander("What do these numbers mean?"):
    st.markdown(
        "**Counties in view** is the number of U.S. counties included after "
        "applying the region filter above.\n\n"
        "**Pearson r** measures how strongly two variables move together. "
        "Here it captures the relationship between a county's industrial emission "
        "intensity and its rate of the selected health condition. A value near 0 "
        "means little to no relationship. A value near 1 would mean a very strong "
        "relationship where higher emissions consistently come with higher disease "
        "rates. In county-level health data, values above roughly 0.2 are considered "
        "a modest but meaningful association.\n\n"
        "**Mean prevalence** is simply the average percentage of adults in the "
        "filtered counties who report having the selected health condition."
    )
 
if n_s1 < 100:
    st.warning(
        f"Only {n_s1:,} counties in this view. "
        "Correlation estimates may be unstable. Try selecting All Regions."
    )
 
# Brush selection for within-visualization cross-chart interaction
brush    = alt.selection_interval(name="county_brush")
trend_s1 = ols_line_df(df_s1, "log_emissions_per_capita", outcome_col_1)
 
# Scatter: log emissions per capita on x, selected outcome on y
scatter_s1 = (
    alt.Chart(df_s1)
    .mark_circle(size=40, opacity=0.5)
    .encode(
        x=alt.X("log_emissions_per_capita:Q", title="Log Emissions Per Capita"),
        y=alt.Y(f"{outcome_col_1}:Q",         title=f"{sel_outcome_1} (%)"),
        ## Highlight brushed counties in a single accent color; grey out unselected
        color=alt.condition(
            brush,
            alt.value(COLOR_ACCENT),
            alt.value("lightgray")
        ),
        tooltip=[
            alt.Tooltip("county_name:N",              title="County"),
            alt.Tooltip("state_abbr:N",               title="State"),
            alt.Tooltip("census_region:N",            title="Region"),
            alt.Tooltip("log_emissions_per_capita:Q", title="Log Emissions PC", format=".2f"),
            alt.Tooltip(f"{outcome_col_1}:Q",         title=f"{sel_outcome_1} (%)", format=".1f"),
        ]
    )
    .properties(width=600, height=480)
    .add_params(brush)
)
 
# OLS trend line layer
trend_line_s1 = (
    alt.Chart(trend_s1)
    .mark_line(color="darkred", strokeDash=[6, 3], strokeWidth=2)
    .encode(
        x=alt.X("log_emissions_per_capita:Q"),
        y=alt.Y(f"{outcome_col_1}:Q")
    )
)
 
# State bar chart: filtered by brush and aggregated in Vega-Lite
state_bar_s1 = (
    alt.Chart(df_s1)
    .mark_bar(color=COLOR_ACCENT, opacity=0.85)
    .encode(
        x=alt.X("mean_val:Q", title=f"Mean {sel_outcome_1} (%)"),
        y=alt.Y("state_abbr:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("state_abbr:N", title="State"),
            alt.Tooltip("mean_val:Q",   title=f"Mean {sel_outcome_1} (%)", format=".1f"),
        ]
    )
    .transform_filter(brush)
    .transform_aggregate(mean_val=f"mean({outcome_col_1})", groupby=["state_abbr"])
    .properties(width=400, height=480)
)
 
# Display the coordinated scatter and state bar
st.altair_chart(
    ((scatter_s1 + trend_line_s1) | state_bar_s1).configure_view(strokeWidth=0),
    use_container_width=False
)
 
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Correlation bar chart (full national dataset, no filter)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Which Outcomes Track With Industrial Emissions?")
st.caption(
    "Pearson r computed for each health outcome vs log emissions per capita "
    "across the full national dataset. Hover for sample size and significance."
)
 
# Pre-compute correlations across the full dataset
corr_rows = []
for label, colname in OUTCOME_MAP.items():
    tmp = df[["log_emissions_per_capita", colname]].dropna()
    if len(tmp) > 2:
        r, p = pearsonr(tmp["log_emissions_per_capita"], tmp[colname])
        corr_rows.append({
            "label": label,
            "r":     round(r, 3),
            "n":     len(tmp),
            "sig":   "p < 0.05" if p < 0.05 else "n.s.",
        })
 
corr_df = pd.DataFrame(corr_rows).sort_values("r", ascending=True)
 
# Horizontal bar chart colored by Pearson r value
corr_bars = (
    alt.Chart(corr_df).mark_bar()
    .encode(
        x=alt.X("r:Q", title="Pearson r  (vs. Log Emissions Per Capita)",
                scale=alt.Scale(domain=[-0.10, 0.35])),
        y=alt.Y("label:N", sort="-x", title=None,
                axis=alt.Axis(labelOverlap=False)),
        color=alt.Color("r:Q",
                        scale=alt.Scale(scheme="redblue", domain=[-0.15, 0.30]),
                        legend=None),
        tooltip=[
            alt.Tooltip("label:N", title="Health Outcome"),
            alt.Tooltip("r:Q",     title="Pearson r", format=".3f"),
            alt.Tooltip("n:Q",     title="Counties (n)"),
            alt.Tooltip("sig:N",   title="Significance"),
        ]
    )
    .properties(
        width=820, height=480,
        title=alt.TitleParams(
            "Health Outcome Correlations with Industrial Emission Intensity",
            subtitle=["Full national dataset  |  Hover for sample size and significance"]
        )
    )
)
 
# Zero reference line
zero_rule = (
    alt.Chart(pd.DataFrame({"r": [0]}))
    .mark_rule(color="black", strokeWidth=1.2)
    .encode(x="r:Q")
)
 
st.altair_chart(corr_bars + zero_rule, use_container_width=False)
 
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Respiratory contrast (COPD vs Current Asthma)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Respiratory Contrast: COPD vs. Current Asthma")
 
# Inline region filter for this section only
sel_region_3 = st.selectbox(
    "Census Region",
    options=REGION_OPTIONS,
    index=0,
    key="region_s3"
)
 
df_s3 = apply_region_filter(df, sel_region_3)
st.caption(
    f"Region: {sel_region_3}  |  "
    "COPD follows an acquired inhalation pathway. Current asthma is primarily "
    "heritable and driven by indoor allergen exposure. The divergence between "
    "the two trends functions as a negative control."
)
 
col_left, col_right = st.columns(2)
 
with col_left:
    # COPD: acquired inhalation pathway, positive trend expected
    st.altair_chart(
        emission_scatter_chart(
            df_s3, "COPD", "COPD Prevalence", "#2166ac",
            "COPD vs. Log Emissions Per Capita",
            "Acquired inhalation injury pathway"
        ).configure_title(fontSize=12, anchor="start"),
        use_container_width=False
    )
 
with col_right:
    # Asthma: heritable and indoor-exposure pathway, near-zero trend expected
    st.altair_chart(
        emission_scatter_chart(
            df_s3, "CASTHMA", "Asthma Prevalence", "#4dac26",
            "Current Asthma vs. Log Emissions Per Capita",
            "Primarily heritable / indoor allergen pathway"
        ).configure_title(fontSize=12, anchor="start"),
        use_container_width=False
    )
 
st.info(
    "The flat asthma trend is a negative control. If industrial emissions were "
    "confounded with all outcomes equally through an unmeasured third variable, "
    "asthma would follow the same pattern as COPD. The divergence supports a "
    "genuine inhalation exposure mechanism for COPD."
)
 
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Neurological and mental health (COGNITION vs Depression)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Neurological and Mental Health Outcomes")
 
# Inline region filter for this section only
sel_region_4 = st.selectbox(
    "Census Region",
    options=REGION_OPTIONS,
    index=0,
    key="region_s4"
)
 
df_s4 = apply_region_filter(df, sel_region_4)
st.caption(
    f"Region: {sel_region_4}  |  "
    "Cognitive disability tracks with industrial emission intensity through "
    "neuroinflammatory and cerebrovascular pathways. Depression is a weaker "
    "signal in this analysis because socioeconomic factors explain more of its "
    "between-county variance than industrial emissions do."
)
 
col_cog, col_dep = st.columns(2)
 
with col_cog:
    # Cognitive disability: neuroinflammatory and cerebrovascular pathway
    st.altair_chart(
        emission_scatter_chart(
            df_s4, "COGNITION", "Cognitive Disability", "#7b2d8b",
            "Cognitive Disability vs. Log Emissions Per Capita",
            "Neuroinflammatory pathway"
        ).configure_title(fontSize=12, anchor="start"),
        use_container_width=False
    )
 
with col_dep:
    # Depression: SES pathway dominant, weaker emissions signal
    st.altair_chart(
        emission_scatter_chart(
            df_s4, "DEPRESSION", "Depression Prevalence", "#b35806",
            "Depression vs. Log Emissions Per Capita",
            "SES pathway dominant"
        ).configure_title(fontSize=12, anchor="start"),
        use_container_width=False
    )
 
# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: Socioeconomic context for depression
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Why Depression Does Not Track With Emissions: The SES Context")
st.caption(
    "The chart below ranks depression's correlation with several socioeconomic "
    "and environmental predictors side by side, so the relative strength of each "
    "one is easy to compare at a glance."
)
 
# Compute correlations of DEPRESSION with SES and emissions predictors
DEP_PREDICTOR_MAP = {
    "Food Insecurity":       "FOODINSECU",
    "Housing Insecurity":    "HOUSINSECU",
    "Lack of Health Insurance": "ACCESS2",
    "Log Emissions Per Capita": "log_emissions_per_capita",
}
 
dep_corr_rows = []
for label, colname in DEP_PREDICTOR_MAP.items():
    tmp = df[[colname, "DEPRESSION"]].dropna()
    if len(tmp) > 2:
        r, p = pearsonr(tmp[colname], tmp["DEPRESSION"])
        dep_corr_rows.append({
            "label": label,
            "r":     round(r, 3),
            "n":     len(tmp),
        })
 
dep_corr_df = pd.DataFrame(dep_corr_rows).sort_values("r", ascending=True)
 
# Ranked bar chart: depression's correlation with each predictor
dep_corr_bars = (
    alt.Chart(dep_corr_df)
    .mark_bar()
    .encode(
        x=alt.X("r:Q", title="Pearson r with Depression Prevalence"),
        y=alt.Y("label:N", sort="-x", title=None,
                axis=alt.Axis(labelOverlap=False)),
        color=alt.condition(
            alt.datum.label == "Log Emissions Per Capita",
            alt.value("#b35806"),
            alt.value("#2166ac")
        ),
        tooltip=[
            alt.Tooltip("label:N", title="Predictor"),
            alt.Tooltip("r:Q",     title="Pearson r", format=".3f"),
            alt.Tooltip("n:Q",     title="Counties (n)"),
        ]
    )
    .properties(
        width=700, height=320,
        title=alt.TitleParams(
            "What Predicts Depression? SES vs. Emissions",
            subtitle=["Orange bar highlights the emissions predictor for comparison"]
        )
    )
)
 
st.altair_chart(dep_corr_bars, use_container_width=False)

