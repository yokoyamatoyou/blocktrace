import pathlib
import sys

import pandas as pd

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from graph import build_edges


def test_classification_and_hops():
    txs = pd.DataFrame(
        [
            {"from": "A", "to": "B", "value": 0.5, "hash": f"h{i}"} for i in range(6)
        ]
        + [
            {"from": "A", "to": "C", "value": 1e-9, "hash": "h6"}
        ]
    )

    def fake_fetcher(address: str) -> pd.DataFrame:
        if address == "B":
            return pd.DataFrame(
                [{"from": "B", "to": "D", "value": 2, "hash": "h7"}]
            )
        return pd.DataFrame()

    edges = build_edges(txs, "A", fetcher=fake_fetcher, max_hop=2)
    edges = edges.sort_values(["src", "dst"]).reset_index(drop=True)

    # Expect three edges: A->B, A->C, B->D
    assert len(edges) == 3

    ab = edges[(edges.src == "A") & (edges.dst == "B")].iloc[0]
    assert ab.laundering
    assert not ab.poisoning

    ac = edges[(edges.src == "A") & (edges.dst == "C")].iloc[0]
    assert ac.poisoning
    assert not ac.laundering

    bd = edges[(edges.src == "B") & (edges.dst == "D")].iloc[0]
    assert bd.hop == 2
