import os
import time
from typing import Literal

import pandas as pd
import requests

BASE_URL = "https://api.bscscan.com/api"
API_KEY = os.getenv("BSCSCAN_KEY", "")


Action = Literal["txlist", "txlistinternal", "tokentx"]


def build_url(action: Action, address: str, start_block: int) -> str:
    """Construct a BscScan API URL for an address."""
    return (
        f"{BASE_URL}?module=account&action={action}&address={address}"
        f"&startblock={start_block}&sort=asc&apikey={API_KEY}"
    )


def fetch_all(action: Action, address: str) -> pd.DataFrame:
    """Fetch all pages for the given action."""
    start, items = 0, []
    while True:
        url = build_url(action, address, start)
        resp = requests.get(url, timeout=10).json()
        data = resp.get("result", [])
        if not data:
            break
        items.extend(data)
        start = int(data[-1]["blockNumber"]) + 1
        time.sleep(0.25)  # keep under 5 req/s
    if not items:
        return pd.DataFrame()
    return pd.json_normalize(items)


def get_transactions(address: str) -> pd.DataFrame:
    """Pull normal, internal, and token transfers for an address."""
    frames = []
    for action in ("txlist", "txlistinternal", "tokentx"):
        df = fetch_all(action, address)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)
