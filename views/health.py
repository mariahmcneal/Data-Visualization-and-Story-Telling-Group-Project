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
        width=360, height=300,
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


# ── Helper: quartile comparison bar chart ──────────────────────────────────────
def emission_quartile_bar(df_src, y_col, y_label, color_scheme="blues"):
    # Drop rows missing either variable before binning
    src = df_src.dropna(subset=["log_emissions_per_capita", y_col]).copy()
    ## Bin counties into four equal-sized groups by emission intensity
    src["emission_quartile"] = pd.qcut(
        src["log_emissions_per_capita"],
        q=4,
        labels=["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"]
    )

    # Aggregate mean outcome value and county count per quartile
    quartile_means = (
        src.groupby("emission_quartile", observed=True)[y_col]
        .agg(mean_val="mean", n_counties="count")
        .reset_index()
    )

    # Bar chart: mean outcome value by emission quartile
    bars = (
        alt.Chart(quartile_means)
        .mark_bar()
        .encode(
            x=alt.X("emission_quartile:N", title="Emissions Per Capita Quartile", sort=None),
            y=alt.Y("mean_val:Q", title=f"Mean {y_label} (%)"),
            color=alt.Color(
                "mean_val:Q",
                scale=alt.Scale(scheme=color_scheme),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("emission_quartile:N", title="Quartile"),
                alt.Tooltip("mean_val:Q",           title=f"Mean {y_label} (%)", format=".2f"),
                alt.Tooltip("n_counties:Q",         title="Counties (n)"),
            ]
        )
        .properties(
            width=320, height=280,
            title=alt.TitleParams(
                f"Mean {y_label} by Emission Quartile",
                subtitle=["Q1 = lowest emitting counties, Q4 = highest emitting counties"]
            )
        )
    )
    return bars


# ── Helper: box plot by emission quartile ──────────────────────────────────────
def emission_quartile_box(df_src, y_col, y_label):
    # Drop rows missing either variable before binning
    src = df_src.dropna(subset=["log_emissions_per_capita", y_col]).copy()
    ## Bin counties into four equal-sized groups by emission intensity
    src["emission_quartile"] = pd.qcut(
        src["log_emissions_per_capita"],
        q=4,
        labels=["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"]
    )

    # Box plot showing the full distribution per quartile, not just the mean
    box = (
        alt.Chart(src)
        .mark_boxplot(extent="min-max", size=32)
        .encode(
            x=alt.X("emission_quartile:N", title="Emissions Per Capita Quartile", sort=None),
            y=alt.Y(f"{y_col}:Q", title=f"{y_label} (%)"),
            color=alt.Color(
                "emission_quartile:N",
                scale=alt.Scale(scheme="blues"),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("emission_quartile:N", title="Quartile"),
                alt.Tooltip(f"{y_col}:Q",           title=y_label, format=".1f"),
            ]
        )
        .properties(
            width=320, height=280,
            title=alt.TitleParams(
                f"Distribution of {y_label} by Emission Quartile",
                subtitle=["Full spread, not just the average"]
            )
        )
    )
    return box


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
        ## Color brushed counties by state; grey out unselected
        color=alt.condition(
            brush,
            alt.Color("state_abbr:N", legend=None),
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
    .properties(width=440, height=360)
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
    .properties(width=300, height=360)
)

# Display the coordinated scatter and state bar
st.altair_chart(
    ((scatter_s1 + trend_line_s1) | state_bar_s1).configure_view(strokeWidth=0),
    use_container_width=False
)

with st.expander("View underlying data"):
    st.dataframe(
        df_s1[["county_name", "state_abbr", "census_region",
               "log_emissions_per_capita", outcome_col_1]]
        .sort_values(outcome_col_1, ascending=False),
        use_container_width=True,
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
        y=alt.Y("label:N", sort="-x", title=None),
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
        width=560, height=320,
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

# ── Quartile comparison: a plainer-language companion to the correlation chart ──
st.markdown("#### A Simpler View: Grouping Counties Into Four Emission Tiers")
st.caption(
    "Pearson r can be hard to interpret at a glance. This chart sorts counties "
    "into four equal-sized groups from lowest to highest emissions and shows the "
    "average prevalence in each group directly."
)

# Curated outcome list for the quartile view, restricted to the strongest signals
QUARTILE_OUTCOME_MAP = {
    "COPD":                 "COPD",
    "Coronary Heart Disease": "CHD",
    "Hearing Disability":    "HEARING",
    "Cognitive Disability":  "COGNITION",
}

sel_quartile_outcome = st.selectbox(
    "Health Outcome for Quartile Comparison",
    options=list(QUARTILE_OUTCOME_MAP.keys()),
    index=0,
    key="outcome_quartile"
)
quartile_col = QUARTILE_OUTCOME_MAP[sel_quartile_outcome]

# Display the quartile bar chart
st.altair_chart(
    emission_quartile_bar(df, quartile_col, sel_quartile_outcome)
    .configure_title(fontSize=12, anchor="start"),
    use_container_width=False
)

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

# ── Box plot: full distribution shift for COPD across emission quartiles ────────
st.markdown("#### Does the Entire Distribution Shift, or Just the Average?")
st.caption(
    "A rising average can hide a lot. This box plot shows the full spread of "
    "COPD prevalence within each emission quartile so you can see whether "
    "high-emission counties are shifted upward as a whole group."
)

st.altair_chart(
    emission_quartile_box(df_s3, "COPD", "COPD Prevalence")
    .configure_title(fontSize=12, anchor="start"),
    use_container_width=False
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
        y=alt.Y("label:N", sort="-x", title=None),
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
        width=520, height=240,
        title=alt.TitleParams(
            "What Predicts Depression? SES vs. Emissions",
            subtitle=["Orange bar highlights the emissions predictor for comparison"]
        )
    )
)

st.altair_chart(dep_corr_bars, use_container_width=False)

# SES scatter charts: food insecurity vs depression, colored by emission quartile
df_ses = df.dropna(
    subset=["FOODINSECU", "DEPRESSION", "log_emissions_per_capita"]
).copy()

## Compute emission intensity quartile for color encoding
df_ses["emissions_q"] = pd.qcut(
    df_ses["log_emissions_per_capita"],
    q=4,
    labels=["Q1 (Low)", "Q2", "Q3", "Q4 (High)"]
)

trend_ses = ols_line_df(df_ses, "FOODINSECU", "DEPRESSION")
r_ses     = df_ses["FOODINSECU"].corr(df_ses["DEPRESSION"])
n_ses     = len(df_ses)

ses_color = alt.Color(
    "emissions_q:N",
    scale=alt.Scale(
        domain=["Q1 (Low)", "Q2", "Q3", "Q4 (High)"],
        range=["#1a9641", "#a6d96a", "#fdae61", "#d7191c"]
    ),
    legend=alt.Legend(title="Emissions Per Capita Quartile")
)

ses_pts = (
    alt.Chart(df_ses)
    .mark_circle(size=40, opacity=0.5)
    .encode(
        x=alt.X("FOODINSECU:Q",  title="Food Insecurity Prevalence (%)"),
        y=alt.Y("DEPRESSION:Q",  title="Depression Prevalence (%)"),
        color=ses_color,
        tooltip=[
            alt.Tooltip("county_name:N",              title="County"),
            alt.Tooltip("state_abbr:N",               title="State"),
            alt.Tooltip("FOODINSECU:Q",               title="Food Insecurity (%)", format=".1f"),
            alt.Tooltip("DEPRESSION:Q",               title="Depression (%)", format=".1f"),
            alt.Tooltip("log_emissions_per_capita:Q", title="Log Emissions PC", format=".2f"),
        ]
    )
)

ses_trend = (
    alt.Chart(trend_ses)
    .mark_line(color="black", strokeDash=[4, 2], strokeWidth=2)
    .encode(
        x=alt.X("FOODINSECU:Q"),
        y=alt.Y("DEPRESSION:Q")
    )
)

ses_chart = (ses_pts + ses_trend).properties(
    width=420, height=340,
    title=alt.TitleParams(
        "Depression vs. Food Insecurity",
        subtitle=[
            f"Colored by emission intensity quartile  |  r = {r_ses:.2f}  |  n = {n_ses:,} counties",
            "No vertical color separation = emissions do not stratify this relationship"
        ]
    )
)

# Repeat the depression vs emissions chart for direct visual comparison
emissions_dep_chart = emission_scatter_chart(
    df, "DEPRESSION", "Depression Prevalence", "#b35806",
    "Depression vs. Log Emissions Per Capita",
    "Same outcome, much weaker predictor"
).properties(width=340, height=340)

st.altair_chart(
    (ses_chart | emissions_dep_chart)
    .configure_title(fontSize=12, anchor="start")
    .configure_view(strokeWidth=0),
    use_container_width=False
)

st.info(
    "Food insecurity (r = {:.2f}) predicts depression far more strongly than "
    "industrial emission intensity. The absence of color separation in the left "
    "chart confirms that counties in the highest emission quartile (red) are not "
    "systematically higher in depression than low-emission counties (green) once "
    "food insecurity is on the x-axis. This supports the conclusion that air "
    "pollution adds incremental mental health burden at most, and that "
    "socioeconomic vulnerability is the dominant driver of county-level "
    "depression prevalence.".format(r_ses)
)