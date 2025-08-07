# BSC Scam Tracker

Streamlit app for tracing BNB Chain addresses. Uses the BscScan API and stores data in DuckDB.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with `BSCSCAN_KEY`.

## Run

```bash
streamlit run app.py
```
