import pandas as pd
from typing import Callable, Set


def _classify(df: pd.DataFrame, src: str, hop: int) -> pd.DataFrame:
    """Aggregate outgoing transactions for a single hop and classify."""
    if df.empty:
        return pd.DataFrame()
    outgoing = df[df["from"].str.lower() == src.lower()]
    if outgoing.empty:
        return pd.DataFrame()
    edges = (
        outgoing.groupby("to")
        .agg(value_native=("value", "sum"), tx_cnt=("hash", "count"))
        .reset_index()
        .rename(columns={"to": "dst"})
    )
    edges["src"] = src
    edges["poisoning"] = edges["value_native"] < 1e-8
    edges["laundering"] = (edges["value_native"] > 1) & (edges["tx_cnt"] > 5)
    edges["hop"] = hop
    return edges[
        [
            "src",
            "dst",
            "value_native",
            "tx_cnt",
            "hop",
            "laundering",
            "poisoning",
        ]
    ]


def build_edges(
    df: pd.DataFrame,
    addr: str,
    fetcher: Callable[[str], pd.DataFrame] | None = None,
    max_hop: int = 1,
    _visited: Set[str] | None = None,
) -> pd.DataFrame:
    """Build multi-hop edge list and classify laundering/poisoning."""

    visited = set() if _visited is None else _visited
    addr_lower = addr.lower()
    if addr_lower in visited:
        return pd.DataFrame(
            columns=[
                "src",
                "dst",
                "value_native",
                "tx_cnt",
                "hop",
                "laundering",
                "poisoning",
            ]
        )
    visited.add(addr_lower)

    edges = _classify(df, addr, hop=1)

    if fetcher is None or max_hop <= 1 or edges.empty:
        return edges

    all_edges = [edges]
    for dst in edges["dst"].unique():
        try:
            sub_df = fetcher(dst)
        except Exception:
            continue
        sub_edges = build_edges(
            sub_df,
            dst,
            fetcher=fetcher,
            max_hop=max_hop - 1,
            _visited=visited,
        )
        if not sub_edges.empty:
            sub_edges["hop"] = sub_edges["hop"] + 1
            all_edges.append(sub_edges)

    if all_edges:
        return pd.concat(all_edges, ignore_index=True, sort=False)
    return pd.DataFrame(
        columns=[
            "src",
            "dst",
            "value_native",
            "tx_cnt",
            "hop",
            "laundering",
            "poisoning",
        ]
    )
