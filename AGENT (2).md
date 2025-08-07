# BSC Scam Tracker – Codex‑Ready Implementation Guide

## 0. Purpose

Build a **Streamlit** application that, given a single BNB‑Chain address (e.g. `0xc8D57802104a37A5d8fA613eC9c678a56A51D24f`), automatically:

1. Pulls *all* on‑chain activity via **BscScan API** (normal, internal, BEP‑20 transfers) within the free 5 req/s limit.
2. Persists raw & transformed data locally (DuckDB) together with evidentiary fields (tx hash, timestamp, block, value, gas, token symbol).
3. Derives a **related address set** (outgoing targets + multi‑hop fan‑outs) and classifies each edge as
   - `laundering` (large, fast fan‑outs / mixers / bridges) or
   - `poisoning` (tiny dust transfers or look‑alike addresses).
4. Presents the evidence through *minimalistic, line‑only* visualisations (no emoji, icons, or colour fill) and a downloadable CSV.

> **Goal:** Deliver forensic artefacts that could be attached to a report or handed over to law enforcement.

---

## 1. Tech Stack (all free‑tier‑friendly)

| Layer    | Tool                                                | Notes                                       |
| -------- | --------------------------------------------------- | ------------------------------------------- |
| Data API | **BscScan API V2**                                  | Community key, 5 req/s, 100k req/day        |
| Storage  | **DuckDB**                                          | single file `scam.db`, columnar, zero setup |
| GUI      | **Streamlit ≥ 1.35**                                | simple Python GUI; hide default menu        |
| Visual   | **Plotly** (scatter, Sankey) & **NetworkX + PyVis** | *line‑only* styling                         |
| Analysis | `pandas`, `numpy`, `python‑Levenshtein`             | heuristics & scoring                        |

---

## 2. Environment & Dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install streamlit duckdb pandas numpy requests plotly networkx pyvis python-levenshtein python-dotenv
```

Place \`\` with `BSCSCAN_KEY=YOUR_API_KEY` alongside `app.py`.

---

## 3. Database Schema (DuckDB)

```sql
-- Raw pull
CREATE TABLE IF NOT EXISTS tx_raw (
  hash TEXT PRIMARY KEY,
  block BIGINT,
  time TIMESTAMP,
  "from" TEXT,
  "to" TEXT,
  value_native DOUBLE,
  token_symbol TEXT,
  gas BIGINT,
  input TEXT
);

-- Derived graph edges (n→n)
CREATE TABLE IF NOT EXISTS tx_edges (
  edge_id BIGINT IDENTITY,
  src TEXT,
  dst TEXT,
  value_usd DOUBLE,
  hop INT,
  laundering BOOL,
  poisoning BOOL,
  PRIMARY KEY(edge_id)
);
```

---

## 4. Core Workflow (pseudo‑Python)

```python
# 1. fetch all pages until empty
def fetch_all(action, address):
    start, items = 0, []
    while True:
        url = build_url(action, address, start)
        data = requests.get(url, timeout=10).json()["result"]
        if not data:
            break
        items.extend(data)
        start = int(data[-1]["blockNumber"]) + 1
        time.sleep(0.25)  # 4 rps < 5 limit
    return pd.json_normalize(items)

# 2. store to DuckDB
con.execute("INSERT OR IGNORE INTO tx_raw SELECT * FROM df")

# 3. build edge list & classify
outgoing = df[df["from"] == addr]
edges = (
    outgoing.groupby("to")
            .agg(value_native=("value", "sum"), tx_cnt=("hash", "count"))
            .reset_index())
edges["poisoning"] = edges["value_native"] < 1e-8
edges["laundering"] = (edges["value_native"] > 1) & (edges["tx_cnt"] > 5)
con.execute("INSERT INTO tx_edges SELECT * FROM edges")
```

---

## 5. Streamlit UI Requirements

1. **Page config & menu removal**

```python
st.set_page_config(
    page_title="BSC Scam Tracker",
    layout="wide",
    menu_items={}  # Removes top‑right hamburger & info icons
)
# Extra CSS to hide help icon
st.markdown("""
    <style>.stActionButtonAvatar {display: none !important;}</style>
    """, unsafe_allow_html=True)
```

2. **Sidebar Inputs**
   - Address text input (default empty, lowercase validation)
   - Date range optional filter
   - Fetch button
3. **Main Tabs**
   - *Metrics*: total tx, total value, edge count
   - *Timeline*: black line scatter (`mode='lines'`)
   - *Sankey*: `link.line.width=1`, `node.color='white'`
   - *Network*: PyVis embed (square nodes, black 1 px edges)
   - *Table*: interactive dataframe + `st.download_button` CSV

---

## 6. Visual Style Guide (line‑only)

| Element    | Plotly/Vis Setting                                |
| ---------- | ------------------------------------------------- |
| Lines      | `color='black', width=1`                          |
| Nodes      | `color='white', line_color='black', line_width=1` |
| Background | `plot_bgcolor='white', paper_bgcolor='white'`     |
| Text       | use default sans‑serif; no emoji                  |

---

## 7. Running Locally

```bash
streamlit run app.py
```

The app automatically creates/updates `scam.db` next to the script.

---

## 8. Suggested File Layout

```
│  .env
│  app.py           # Streamlit UI + logic
│  db.py            # DuckDB helpers
│  bscscan.py       # API wrappers
│  graph.py         # classification & graph build
│  requirements.txt
```

---

## 9. Testing Checklist for Codex

-

---

## 10. Deployment (optional)

*Streamlit Community Cloud* can host 3 apps free; push repo to GitHub and add `BSCSCAN_KEY` as a secret. DuckDB persists in the app filesystem; for multi‑user writes, switch to Supabase.

---

**End of Guide – Ready for Codex**

