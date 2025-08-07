import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "scam.db"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(DB_PATH)
    return con


def init_db(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
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
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS tx_edges (
            edge_id BIGINT IDENTITY,
            src TEXT,
            dst TEXT,
            value_native DOUBLE,
            tx_cnt BIGINT,
            hop INT,
            laundering BOOL,
            poisoning BOOL,
            PRIMARY KEY(edge_id)
        );
        """
    )


def insert_raw(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    if df.empty:
        return
    con.execute(
        "INSERT OR IGNORE INTO tx_raw SELECT * FROM df",
        {"df": df[
            [
                "hash",
                "blockNumber",
                "timeStamp",
                "from",
                "to",
                "value",
                "tokenSymbol",
                "gas",
                "input",
            ]
        ].rename(
            columns={
                "blockNumber": "block",
                "timeStamp": "time",
                "value": "value_native",
                "tokenSymbol": "token_symbol",
            }
        )},
    )


def insert_edges(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    if df.empty:
        return
    con.execute("INSERT INTO tx_edges SELECT * FROM df", {"df": df})
