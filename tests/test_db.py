import pathlib
import sys

import duckdb
import pandas as pd

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from db import insert_raw


def test_insert_raw_handles_missing_columns():
    con = duckdb.connect(":memory:")
    con.execute(
        """
        CREATE TABLE tx_raw (
            hash TEXT PRIMARY KEY,
            block BIGINT,
            time TIMESTAMP,
            "from" TEXT,
            "to" TEXT,
            value_native DOUBLE,
            token_symbol TEXT,
            gas BIGINT,
            input TEXT
        )
        """
    )

    df = pd.DataFrame(
        [
            {
                "hash": "h1",
                "blockNumber": 1,
                "timeStamp": pd.Timestamp("2024-01-01"),
                "from": "A",
                "to": "B",
                "value": 0.1,
                # tokenSymbol, gas, input missing
            }
        ]
    )

    insert_raw(con, df)

    row = con.execute(
        "SELECT token_symbol, gas, input FROM tx_raw WHERE hash='h1'"
    ).fetchone()
    assert row == (None, None, None)
