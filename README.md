# 🌿 RivetLab

Interactive ecological food-web visualization and extinction simulation, inspired by the Rivet Popper Hypothesis.

RivetLab demonstrates how removing species from an ecological network can affect its structure, connectivity, and robustness. It is a **topological simulation** for exploration and education — it does not predict real population dynamics or validated extinction outcomes.

---

## Live demo

Deploy to [Streamlit Community Cloud](https://streamlit.io/cloud) using the instructions below.

---

## Dataset

The application ships with a real ecological food-web dataset from the [Mangal](https://mangal.io) database:

- **Network:** Havens 1992 — Beaver Lake
- **Species:** 56
- **Interactions:** 267
- **Reference:** Havens, K. E. (1992). Scale and structure in natural food webs. *Science*, 257(5073), 1107-1109.
- **DOI:** [10.1126/science.257.5073.1107](https://doi.org/10.1126/science.257.5073.1107)
- **Source:** [mangal.io](https://mangal.io) network ID `1219`

The raw Mangal records store directed trophic interactions as **consumer → resource**. RivetLab reverses these edges so the application convention is **resource → consumer**.

Processed data are stored locally in:

- `data/nodes.csv`
- `data/edges.csv`
- `data/dataset_info.json`

The deployed application reads these local files and does not require a live Mangal API connection.

---

## Features

1. **Home / Overview** — project introduction, dataset attribution, and key statistics.
2. **Explore Food Web** — interactive Plotly network with search, highlighting, and filtering.
3. **Extinction Simulator** — manual, random, degree-based, and betweenness-based removal with cascading secondary extinctions.
4. **Ecosystem Experiments** — compare random, degree, and betweenness removal strategies; survival curves; R50 robustness metric.
5. **Graph Analytics** — centrality rankings, degree distributions, generality vs. vulnerability, and downloadable tables.
6. **Methodology** — dataset source, processing steps, graph construction, assumptions, and limitations.

---

## Technology stack

- Python 3.10+
- Streamlit ≥ 1.35
- NetworkX
- Plotly
- Pandas
- NumPy
- Pytest

---

## Run locally

```powershell
# 1. Clone the repository
git clone https://github.com/<your-username>/rivetlab.git
cd rivetlab

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Run tests

```powershell
pytest tests/test_simulation.py -v
```

---

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub:

```powershell
git init
git add .
git commit -m "Initial RivetLab commit"
git branch -M main
git remote add origin https://github.com/<your-username>/rivetlab.git
git push -u origin main
```

2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud), sign in with GitHub, and click **New app**.
3. Select your repository, branch `main`, and main file path `app.py`.
4. Streamlit Cloud will read `runtime.txt` and use **Python 3.12**.
5. Click **Deploy**.

No secrets or environment variables are required.

> **Note:** The local environment used to build this project has Python 3.14. Streamlit Community Cloud does not support Python 3.14, so `runtime.txt` pins the deployment runtime to Python 3.12. If you install locally on Python 3.14, `pip install -r requirements.txt` will resolve the latest versions that have wheels for 3.14.

---

## Project structure

```
RivetLab/
├── app.py                         # Home page
├── pages/
│   ├── 1_Explore_Food_Web.py
│   ├── 2_Extinction_Simulator.py
│   ├── 3_Ecosystem_Experiments.py
│   ├── 4_Graph_Analytics.py
│   └── 5_Methodology.py
├── src/
│   ├── data_loader.py             # CSV → NetworkX DiGraph
│   ├── metrics.py                 # Graph analytics
│   ├── simulation.py              # Extinction engine
│   ├── experiments.py             # Random & targeted removal experiments
│   ├── plotting.py                # Plotly figures
│   └── theme.py                   # UI helpers
├── data/
│   ├── nodes.csv
│   ├── edges.csv
│   └── dataset_info.json
├── tests/
│   └── test_simulation.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README.md
```

---

## Scientific limitations

- The model is purely structural. It ignores population abundances, interaction strengths, environmental variability, and functional redundancy.
- Edge direction in the Havens 1992 Mangal record is marked as "unknown"; RivetLab infers resource → consumer direction from interaction type and known species ecology, consistent with directed records in other Mangal food webs.
- Results should not be interpreted as validated ecological predictions.

---

## License

This project is provided for educational use. Dataset attribution belongs to the original authors and Mangal.
