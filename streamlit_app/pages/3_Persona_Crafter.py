"""
3_Persona_Crafter.py — demographics, self-report items, and cognitive
formulation for the selected patient.
"""

import sys
from pathlib import Path

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

import pandas as pd
import streamlit as st

from components.graph import render_cognitive_graph
from components.sidebar import render_sidebar_selector

st.set_page_config(page_title="Persona Crafter", layout="wide")
st.title("Persona Crafter")

experiment_dir, persona_data = render_sidebar_selector()

if persona_data is None:
    st.info("Select an experiment and persona from the sidebar to begin.")
    st.stop()

demo        = persona_data.get("demographics", {})
self_report = persona_data.get("self_report", {})
agg_edges   = persona_data.get("agg_edges", {})
persona_id  = persona_data.get("persona_id", "?")
demo_val_attempts = persona_data.get("demographics_validation_attempts", [])
sr_val_attempts   = persona_data.get("selfreport_validation_attempts", [])

st.subheader(f"Persona {persona_id}")

# ── Demographics ───────────────────────────────────────────────────────────

st.markdown("#### Demographics")

demo_fields = [
    ("Age",                 demo.get("age", "N/A")),
    ("Gender",              demo.get("gender", "N/A")),
    ("Ethnicity",           demo.get("ethnicity", "N/A")),
    ("Relationship Status", demo.get("relationship_status", "N/A")),
    ("Occupation",          demo.get("occupation", "N/A")),
    ("Trauma Type",         demo.get("trauma_type", "N/A")),
    ("PCL-5",               demo.get("pcl5", "N/A")),
]

demo_html = "".join(
    f"<span style='margin-right:2rem'><span style='font-size:0.75rem;color:#888;display:block'>{label}</span>"
    f"<span style='font-size:0.9rem;font-weight:600'>{value}</span></span>"
    for label, value in demo_fields
)
st.markdown(
    f"<div style='display:flex;flex-wrap:wrap;gap:0.5rem 0;padding:0.5rem 0'>{demo_html}</div>",
    unsafe_allow_html=True,
)

# ── Self-report items ──────────────────────────────────────────────────────

st.divider()
st.markdown("#### Self-Report Items")

NODE_ORDER = [
    "Triggers",
    "Memory",
    "Negative Appraisals",
    "Threat",
    "Maladaptive Strategies",
]

if self_report:
    rows = []
    for node in NODE_ORDER:
        items = self_report.get(node, [])
        if not items:
            continue
        item_texts = []
        for item in items:
            if isinstance(item, dict):
                item_texts.append(f"{item.get('key', '')}: {item.get('value', '')}")
            else:
                item_texts.append(str(item))
        rows.append({"Component": node, "Items": "\n".join(item_texts)})

    df_sr = pd.DataFrame(rows)
    st.dataframe(df_sr, use_container_width=True, hide_index=True, column_config={
        "Items": st.column_config.TextColumn(width="large"),
    })
else:
    st.info("No self-report data available for this persona.")

# ── Validation attempts ────────────────────────────────────────────────────

if demo_val_attempts or sr_val_attempts:
    st.divider()
    st.markdown("#### Persona Validation")

    if demo_val_attempts:
        st.markdown("**Demographics**")
        for att in demo_val_attempts:
            status = "PASS" if att.get("passed") else "FAIL"
            icon   = "✅" if att.get("passed") else "❌"
            with st.expander(f"{icon} Attempt {att.get('attempt', '?')} — {status}", expanded=False):
                for issue in att.get("issues", []):
                    st.markdown(f"- **{issue.get('field')}**: {issue.get('explanation')}")

    if sr_val_attempts:
        st.markdown("**Self-Report**")
        for att in sr_val_attempts:
            status = "PASS" if att.get("passed") else "FAIL"
            icon   = "✅" if att.get("passed") else "❌"
            with st.expander(f"{icon} Attempt {att.get('attempt', '?')} — {status}", expanded=False):
                for issue in att.get("issues", []):
                    st.markdown(f"- **{issue.get('component')} / {issue.get('item')}**: {issue.get('explanation')}")

# ── Cognitive formulation ──────────────────────────────────────────────────

st.divider()
st.subheader("Cognitive Formulation (Aggregated EMA)")

graph_col, table_col = st.columns([2, 1])

with graph_col:
    if agg_edges:
        fig = render_cognitive_graph(agg_edges)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No aggregated edge data available.")

with table_col:
    if agg_edges:
        st.markdown("**Edge weights**")
        edge_rows = [
            {"Edge": k.replace(" -- ", " → "), "Weight": round(v, 4)}
            for k, v in agg_edges.items()
        ]
        if edge_rows:
            st.dataframe(pd.DataFrame(edge_rows), use_container_width=True, hide_index=True,
                         height=(len(edge_rows) + 1) * 35 + 3)
        else:
            st.info("All edge weights are zero.")
