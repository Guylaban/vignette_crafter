"""
7_Embedding_Clusters.py — cluster vignettes by semantic embedding and compare
conditions (full / no_formulation / zero_shot) for a selected model.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

from utils.loader import get_experiments

st.set_page_config(page_title="Embedding Clusters", layout="wide")
st.title("Vignette Embedding Clusters")

# ── Discover available (model, condition) runs ────────────────────────────────

REPO_ROOT  = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "output"


@st.cache_data
def discover_runs() -> pd.DataFrame:
    rows = []
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir():
            continue
        files = list(d.glob("experiment_*.json"))
        if not files:
            continue
        try:
            with open(files[0], encoding="utf-8") as f:
                cfg = json.load(f).get("config", {})
            model     = next(iter(cfg.get("models", {}).values()), None)
            condition = cfg.get("vignette_mode")
            if model and condition:
                rows.append({"dir": d, "model": model, "condition": condition, "n": len(files)})
        except Exception:
            continue
    return pd.DataFrame(rows)


runs = discover_runs()

# ── Sidebar controls ──────────────────────────────────────────────────────────

st.sidebar.header("Settings")

available_models = sorted(runs["model"].unique())
selected_model   = st.sidebar.selectbox("Model", available_models, index=available_models.index("gpt-5.4") if "gpt-5.4" in available_models else 0)

model_runs = runs[runs["model"] == selected_model]

CONDITION_LABELS = {
    "full":           "Full formulation",
    "no_formulation": "No formulation",
    "zero_shot":      "Zero-shot",
}
CONDITION_COLORS = {
    "Full formulation": "#28a745",
    "No formulation":   "#007bff",
    "Zero-shot":        "#fd7e14",
}

available_conditions = model_runs["condition"].tolist()
selected_conditions  = st.sidebar.multiselect(
    "Conditions", options=list(CONDITION_LABELS.keys()),
    default=[c for c in CONDITION_LABELS if c in available_conditions],
    format_func=lambda c: CONDITION_LABELS[c],
)

max_pid = int(model_runs["n"].max()) if not model_runs.empty else 500
persona_range = st.sidebar.slider("Persona IDs", min_value=1, max_value=max_pid, value=(1, 10))
n_clusters    = st.sidebar.slider("K-means clusters (k)", min_value=2, max_value=8, value=3)
emb_model     = st.sidebar.selectbox("Embedding model", ["both", "all-MiniLM-L6-v2", "MentalBERT"])

# ── Load vignettes ────────────────────────────────────────────────────────────

@st.cache_data
def load_vignettes(model: str, conditions: list, pid_min: int, pid_max: int) -> pd.DataFrame:
    rows = []
    for condition in conditions:
        match = runs[(runs["model"] == model) & (runs["condition"] == condition)]
        if match.empty:
            continue
        dirpath = match.sort_values("n", ascending=False).iloc[0]["dir"]
        for pid in range(pid_min, pid_max + 1):
            fp = dirpath / f"experiment_{pid}.json"
            if not fp.exists():
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                text = data.get("vignette", "").strip()
                if not text:
                    continue
                rows.append({
                    "persona_id": pid,
                    "condition":  condition,
                    "label":      CONDITION_LABELS[condition],
                    "vignette":   text,
                    "preview":    text[:120] + "…",
                })
            except Exception:
                continue
    return pd.DataFrame(rows)


if not selected_conditions:
    st.info("Select at least one condition.")
    st.stop()

df = load_vignettes(selected_model, selected_conditions, persona_range[0], persona_range[1])
st.caption(f"{len(df)} vignettes — {selected_model}, personas {persona_range[0]}–{persona_range[1]}")

if df.empty:
    st.error("No vignettes found for the selected options.")
    st.stop()

# ── Embedding models ──────────────────────────────────────────────────────────

@st.cache_resource
def load_minilm():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_resource
def load_mentalbert():
    import torch
    from transformers import AutoTokenizer, AutoModel
    import os
    from huggingface_hub import get_token
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    token = get_token() or os.environ.get("HF_TOKEN")
    tok = AutoTokenizer.from_pretrained("mental/mental-bert-base-uncased", token=token)
    mdl = AutoModel.from_pretrained("mental/mental-bert-base-uncased", token=token)
    mdl.eval()
    return tok, mdl


def encode_minilm(texts: list) -> np.ndarray:
    return load_minilm().encode(texts, show_progress_bar=False)


def encode_mentalbert(texts: list) -> np.ndarray:
    import torch
    tok, mdl = load_mentalbert()
    all_embs = []
    batch_size = 8
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        enc = tok(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            out = mdl(**enc)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        emb  = (out.last_hidden_state * mask).sum(1) / mask.sum(1)
        all_embs.append(emb.numpy())
    return np.vstack(all_embs)


ENCODERS = {
    "all-MiniLM-L6-v2": encode_minilm,
    "MentalBERT":        encode_mentalbert,
}

names_to_load = ("all-MiniLM-L6-v2", "MentalBERT") if emb_model == "both" else (emb_model,)

with st.spinner("Loading embedding model(s)…"):
    if "all-MiniLM-L6-v2" in names_to_load:
        load_minilm()
    if "MentalBERT" in names_to_load:
        load_mentalbert()

# ── Embed + PCA + KMeans ──────────────────────────────────────────────────────

@st.cache_data
def compute_plot_df(texts: tuple, model_name: str, k: int) -> pd.DataFrame:
    embs   = ENCODERS[model_name](list(texts))
    coords = PCA(n_components=2, random_state=42).fit_transform(embs)
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(coords)
    return pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "cluster": labels.astype(str)})


texts = tuple(df["vignette"].tolist())
cols  = st.columns(len(names_to_load))

for col, name in zip(cols, names_to_load):
    with col:
        with st.spinner(f"Embedding with {name}…"):
            plot_df = pd.concat([df.reset_index(drop=True),
                                 compute_plot_df(texts, name, n_clusters)], axis=1)

        fig = px.scatter(
            plot_df, x="x", y="y",
            color="label",
            symbol="cluster",
            hover_data={"persona_id": True, "preview": True,
                        "x": False, "y": False, "cluster": False},
            title=name,
            labels={"label": "Condition", "cluster": "Cluster"},
            color_discrete_map=CONDITION_COLORS,
            height=500,
        )
        fig.update_traces(marker=dict(size=11, opacity=0.85))
        fig.update_layout(legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

# ── Vignette inspector ────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Vignette inspector")
pid = st.selectbox("Persona ID", sorted(df["persona_id"].unique()))
for _, row in df[df["persona_id"] == pid].sort_values("condition").iterrows():
    with st.expander(row["label"]):
        st.write(row["vignette"])
