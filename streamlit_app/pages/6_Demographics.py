"""
6_Demographics.py — aggregate demographics charts for a selected experiment.
"""

import sys
from pathlib import Path

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st

_PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys as _sys
if str(_PROJECT_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_PROJECT_ROOT))

from configs.demographics import OCCUPATION_GROUPS
from utils.loader import get_experiments, get_personas, load_persona

st.set_page_config(page_title="Demographics", layout="wide")
st.title("Demographics")


def _load_demographics(experiment_dir: Path) -> pd.DataFrame:
    rows = []
    for p in get_personas(experiment_dir):
        try:
            data = load_persona(p["path"])
        except Exception:
            continue
        demo = data.get("demographics", {})
        rows.append({
            "age":                 demo.get("age"),
            "gender":              demo.get("gender"),
            "ethnicity":           demo.get("ethnicity"),
            "relationship_status": demo.get("relationship_status"),
            "occupation":          demo.get("occupation"),
            "trauma_type":         demo.get("trauma_type"),
            "pcl5":                demo.get("pcl5"),
        })
    return pd.DataFrame(rows)


experiments = get_experiments()

if not experiments:
    st.info("No experiments found. Run `python main.py` to generate data.")
    st.stop()

exp_names = [e["name"] for e in experiments]
selected_name = st.selectbox("Select experiment", exp_names)
selected_exp = next(e for e in experiments if e["name"] == selected_name)

df = _load_demographics(selected_exp["path"])

if df.empty:
    st.warning("No persona data found in this experiment.")
    st.stop()

n = len(df)
st.markdown(f"**{n} persona{'s' if n != 1 else ''}** loaded.")

# ── Row 1: Age + PCL-5 ────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df.dropna(subset=["age"]),
        x="age",
        nbins=20,
        title="Age Distribution",
        labels={"age": "Age"},
        color_discrete_sequence=["#8CBBED"],
    )
    fig.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        df.dropna(subset=["pcl5"]),
        x="pcl5",
        nbins=15,
        title="PCL-5 Score Distribution",
        labels={"pcl5": "PCL-5 Score"},
        color_discrete_sequence=["#FA9F9F"],
    )
    fig.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Gender + Relationship Status ───────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    gender_counts = df["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]
    fig = px.bar(
        gender_counts,
        x="gender",
        y="count",
        text="count",
        title="Gender",
        labels={"gender": "", "count": "Count"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col4:
    rs_counts = df["relationship_status"].value_counts().reset_index()
    rs_counts.columns = ["relationship_status", "count"]
    fig = px.bar(
        rs_counts,
        x="relationship_status",
        y="count",
        text="count",
        title="Relationship Status",
        labels={"relationship_status": "", "count": "Count"},
        color_discrete_sequence=["#72B7B2"],
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Ethnicity ──────────────────────────────────────────────────────────
eth_counts = df["ethnicity"].value_counts().reset_index()
eth_counts.columns = ["ethnicity", "count"]
fig = px.bar(
    eth_counts,
    x="ethnicity",
    y="count",
    text="count",
    title="Ethnicity",
    labels={"ethnicity": "", "count": "Count"},
    color_discrete_sequence=["#FACA7E"],
)
fig.update_traces(textposition="outside")
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)

# ── Row 4: Trauma Type ────────────────────────────────────────────────────────
trauma_counts = df["trauma_type"].value_counts().reset_index()
trauma_counts.columns = ["trauma_type", "count"]
fig = px.bar(
    trauma_counts,
    x="count",
    y="trauma_type",
    text="count",
    orientation="h",
    title="Trauma Type",
    labels={"trauma_type": "", "count": "Count"},
    color_discrete_sequence=["#D4C1F8"],
)
fig.update_traces(textposition="outside")
fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=max(300, len(trauma_counts) * 28),
)
st.plotly_chart(fig, use_container_width=True)

# ── Row 5: Occupation ─────────────────────────────────────────────────────────
df["occupation_group"] = df["occupation"].map(OCCUPATION_GROUPS).fillna("Other")
grp_counts = df["occupation_group"].value_counts().reset_index()
grp_counts.columns = ["group", "count"]
fig = px.bar(
    grp_counts,
    x="group",
    y="count",
    text="count",
    title="Occupation Group",
    labels={"group": "", "count": "Count"},
    color_discrete_sequence=["#76C87E"],
)
fig.update_traces(textposition="outside")
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)
