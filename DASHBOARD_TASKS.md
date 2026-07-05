# Dashboard Project — Task List & Team Breakdown

**Live app:** https://data-visualization-and-story-telling-group-project.streamlit.app/

This breaks down what's left to finish the dashboard assignment, with a proposed owner
for each task based on who worked on that part of the EDA notebook. Reassign anything
that doesn't fit — this is a starting point, not a mandate.

---

## What's already done

- [x] Merged dataset cleaned and loaded (`merged_env_health_2023.csv`)
- [x] Skeleton `app.py` deployed to Streamlit Cloud with:
  - Sidebar dropdowns for X/Y variable selection across SES, AQI, Emissions, Health
  - State filter
  - Linked scatter (brush select) + bar chart by state
  - Tooltips on the scatter plot
  - Histogram + data table
- [x] `Dashboard_Data_Prep.ipynb` for prototyping new chart ideas before adding to `app.py`
- [x] GitHub workflow README (branching, PRs, avoiding overwrites)
- [x] PPTX report outline (placeholders for screenshots + descriptions)

---

## Remaining tasks

### 1. Dashboard code (`app.py`)

| Task | Suggested owner | Why |
|---|---|---|
| Add a county-level choropleth map as a third coordinated view | **Mariah** | Her EDA section already built "Chart 6: Choropleth Map" for emissions — closest starting point |
| Review/extend the `EMISSIONS` variable options and labels in `VARIABLE_GROUPS` | **Mariah** | Owned emissions charts (histograms, top-15 states, per-capita) in the EDA |
| Add a minimum sample-size guard so the state bar chart doesn't show noisy means from 1–2 brushed counties | **Michelle** | Did the missingness/coverage analysis, most familiar with where data is sparse |
| Review/extend the `SES` variable options and labels; add plain-language descriptions for each SES variable | **Michelle** | Owned the SES missingness and definitions section |
| Add a second coordinated view focused on health outcomes (e.g., health variable distribution split by a brushed selection) | **Dalis** | Owned the health outcome distribution and pollution/health research questions |
| Review/extend the `HEALTH` variable options and labels; add plain-language descriptions | **Dalis** | Same as above |
| Cross-check all four variable groups still match the EDA notebook's `SES` / `AQI` / `EMISSIONS` / `HEALTH` lists | **Whoever picks it up first** | Quick sanity pass, no deep context needed |

### 2. Testing / QA

- [ ] Each person tests every variable pair in their assigned category (watch for
      variables with heavy missingness, like AQI, which only covers ~500 counties)
- [ ] Confirm the app still boots cleanly after each merge to `main` (Streamlit Cloud
      redeploys automatically — check the live link a minute or two after merging)
- [ ] One pass by someone who *didn't* write a given section, to catch anything
      confusing to a first-time user

### 3. PDF / PPTX report

Each feature slide needs a real screenshot once the corresponding app feature is final.

| Slide | Suggested owner |
|---|---|
| Overview | **Mariah** (built the skeleton, knows the overall structure) |
| UI Interaction (dropdowns + filters) | **Michelle** |
| Within-visualization interaction (brushing) | **Mariah** |
| Tooltip | **Dalis** |
| Coordinated visualizations | Whoever adds the second/third coordinated view |
| Trade-offs & limitations | **All three** — add a bullet each from your own section |
| Moving forward | **All three** — quick group pass |

### 4. Deployment / GitHub

- [ ] Everyone clones the repo and confirms `requirements.txt` installs cleanly
- [ ] Work happens on individual branches, merged via Pull Request (see `README.md`)
- [ ] Update `requirements.txt` if anyone adds a new Python package
- [ ] Final check that the live Streamlit link reflects the latest `main` before submitting

---

## Suggested order of operations

1. Everyone pulls `main`, reads `README.md`, does a practice branch/PR if new to Git
2. Code tasks (Section 1) happen in parallel on separate branches
3. Merge one at a time, re-testing the live app after each merge
4. Once code is finalized, take screenshots and fill in the PPTX
5. Final review of both the live app and the PPTX before submission
