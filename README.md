# Environmental & Community Health Explorer

Interactive Streamlit dashboard exploring how socioeconomic conditions, air quality,
greenhouse gas emissions, and health outcomes relate to one another across U.S. counties (2023 data).

**Live app:** https://data-visualization-and-story-telling-group-project.streamlit.app/

---

## Files in this repo

| File | Purpose |
|---|---|
| `app.py` | The deployed Streamlit dashboard. This is what Streamlit Cloud runs. |
| `requirements.txt` | Python packages the app needs. Update this if you add a new import. |
| `merged_env_health_2023.csv` | The cleaned dataset the app reads. |
| `Dashboard_Data_Prep.ipynb` | Scratch notebook for prototyping chart ideas before adding them to `app.py`. Not run by the live app. |

---

## Golden rule: don't overwrite each other's work

Streamlit Cloud only looks at whatever is on the `main` branch of this repo, so if two
people edit `app.py` directly on `main` at the same time, whoever pushes second can
silently erase the other person's changes. The workflow below prevents that.

**Every time you sit down to work, in this order:**
1. Pull the latest code
2. Make a branch for your section
3. Edit *only* your section
4. Commit and push your branch
5. Open a Pull Request, don't push straight to `main`

---

## One-time setup

1. Install Git if you don't have it: https://git-scm.com/downloads
2. Clone the repo (do this once):
   ```bash
   git clone https://github.com/<org-or-username>/<repo-name>.git
   cd <repo-name>
   ```
3. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## Every time you start working

### 1. Get the latest version of the code

```bash
git checkout main
git pull origin main
```

This downloads everyone else's latest changes so you're not working off a stale copy.

### 2. Create a branch for your section

Never edit `app.py` directly on `main`. Make a branch named after what you're working on:

```bash
git checkout -b add-map-view
```

(Examples: `add-map-view`, `fix-tooltip-formatting`, `dalis-health-section`.)

### 3. Edit only your section

Open `app.py` and change **only the part you're responsible for**. A few habits that
prevent accidental overwrites:

- Don't reformat, rename, or "clean up" code outside your section, even if you think it
  looks messy — that turns a small change into one giant diff that's impossible to review.
- If you're adding a new chart or feature, add a new function/section rather than
  rewriting an existing one.
- If you genuinely need to change shared code (like `load_data()` or `VARIABLE_GROUPS`),
  say so in your group chat first so nobody else is editing the same lines at the same time.

### 4. Save your progress with Git

Check what changed:
```bash
git status
git diff
```

Stage and commit **only your changes**:
```bash
git add app.py
git commit -m "Add choropleth map view for GHG emissions"
```

Write commit messages that describe *what* changed, not "update" or "fix stuff."

### 5. Push your branch (not `main`)

```bash
git push origin add-map-view
```

This uploads your branch to GitHub. It does **not** touch `main` or anyone else's code.

### 6. Open a Pull Request (PR)

1. Go to the repo on GitHub — you'll see a banner "Compare & pull request." Click it.
2. Add a short description of what you changed.
3. Ask a teammate to look it over, or just look it over yourself if you're pressed for time.
4. Click **Merge pull request** to bring your changes into `main`.

Streamlit Cloud automatically redeploys the app a minute or two after `main` updates —
no separate deploy step needed.

### 7. Clean up (optional but tidy)

```bash
git checkout main
git pull origin main
git branch -d add-map-view
```

---

## If Git says there's a "merge conflict"

This means two people changed the same lines of `app.py`. It's not a crisis — Git will
mark both versions in the file like this:

```
<<<<<<< HEAD
your version of the line
=======
their version of the line
>>>>>>> main
```

Open the file, decide which version (or combination) is correct, delete the `<<<<<<<`,
`=======`, and `>>>>>>>` markers, save, then:

```bash
git add app.py
git commit -m "Resolve merge conflict in app.py"
git push origin <your-branch-name>
```

If you're not sure how to resolve it, don't guess under time pressure — post the
conflicted section in the group chat and sort it out together before pushing.

---

## Quick reference

| Command | What it does |
|---|---|
| `git pull origin main` | Get the latest code from GitHub |
| `git checkout -b <branch-name>` | Create and switch to a new branch |
| `git status` | See what files you've changed |
| `git add <file>` | Stage a file to be committed |
| `git commit -m "message"` | Save a snapshot of your staged changes |
| `git push origin <branch-name>` | Upload your branch to GitHub |

**Rule of thumb:** if you're about to type `git push origin main`, stop — you almost
always want to push a branch and open a PR instead.
