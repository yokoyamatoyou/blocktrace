import os
from io import StringIO

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

import bscscan
import db
import graph

# Page configuration
st.set_page_config(
    page_title="BSC Scam Tracker",
    layout="wide",
    menu_items={},
)
st.markdown(
    """
    <style>.stActionButtonAvatar {display: none !important;}</style>
    """,
    unsafe_allow_html=True,
)

load_dotenv()

# Database
con = db.connect()
db.init_db(con)

with st.sidebar:
    address = st.text_input("Address", placeholder="bnb address", value="").lower()
    date_range = st.date_input("Date range", [])
    fetch = st.button("Fetch")

if fetch and address:
    tx_df = bscscan.get_transactions(address)
    if not tx_df.empty:
        # convert timestamps
        if "timeStamp" in tx_df.columns:
            tx_df["timeStamp"] = pd.to_datetime(tx_df["timeStamp"], unit="s")
            if len(date_range) == 2:
                start, end = date_range
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end) + pd.Timedelta(days=1)
                tx_df = tx_df[
                    (tx_df["timeStamp"] >= start_dt)
                    & (tx_df["timeStamp"] < end_dt)
                ]
        db.insert_raw(con, tx_df)
        edges = graph.build_edges(
            tx_df, address, fetcher=bscscan.get_transactions, max_hop=2
        )
        db.insert_edges(con, edges)
    else:
        st.warning("No transactions found")

if 'tx_df' not in locals() or tx_df.empty:
    st.stop()

metrics_tab, timeline_tab, sankey_tab, network_tab, table_tab = st.tabs(
    ["Metrics", "Timeline", "Sankey", "Network", "Table"]
)

with metrics_tab:
    st.write(f"Total tx: {len(tx_df)}")
    st.write(f"Total value: {tx_df['value'].astype(float).sum()}")
    st.write(f"Edge count: {len(edges)}")

with timeline_tab:
    if "timeStamp" in tx_df.columns:
        timeline = tx_df.sort_values("timeStamp")
        fig = go.Figure(
            go.Scatter(
                x=timeline["timeStamp"],
                y=timeline["value"].astype(float),
                mode="lines",
                line=dict(color="black", width=1),
            )
        )
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with sankey_tab:
    if not edges.empty:
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(label=[address] + edges["dst"].tolist(), color="white"),
                    link=dict(
                        source=[0] * len(edges),
                        target=list(range(1, len(edges) + 1)),
                        value=edges["value_native"].astype(float),
                        line=dict(color="black", width=1),
                    ),
                )
            ]
        )
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with network_tab:
    if not edges.empty:
        G = nx.DiGraph()
        for _, row in edges.iterrows():
            G.add_edge(row["src"], row["dst"], value=row["value_native"])
        net = Network(height="500px", width="100%", bgcolor="white")
        net.from_nx(G)
        net.set_options(
            """
            var options = {
                "edges": {"color": {"color": "black"}, "width": 1},
                "nodes": {
                    "shape": "box",
                    "color": {"background": "white", "border": "black"},
                    "borderWidth": 1
                }
            }
            """
        )
        html = net.generate_html("graph.html")
        with open("graph.html") as f:
            st.components.v1.html(f.read(), height=500)

with table_tab:
    st.dataframe(edges)
    csv = edges.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="edges.csv", mime="text/csv")
