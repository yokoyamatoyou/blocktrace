import pandas as pd


def build_edges(df: pd.DataFrame, addr: str) -> pd.DataFrame:
    """Build edge list from outgoing transactions and classify."""
    if df.empty:
        return pd.DataFrame(columns=[
            "src",
            "dst",
            "value_native",
            "tx_cnt",
            "hop",
            "laundering",
            "poisoning",
        ])
    outgoing = df[df["from"].str.lower() == addr.lower()]
    edges = (
        outgoing.groupby("to")
        .agg(value_native=("value", "sum"), tx_cnt=("hash", "count"))
        .reset_index()
        .rename(columns={"to": "dst"})
    )
    edges["src"] = addr
    edges["poisoning"] = edges["value_native"] < 1e-8
    edges["laundering"] = (edges["value_native"] > 1) & (edges["tx_cnt"] > 5)
    edges["hop"] = 1
    return edges[[
        "src",
        "dst",
        "value_native",
        "tx_cnt",
        "hop",
        "laundering",
        "poisoning",
    ]]
