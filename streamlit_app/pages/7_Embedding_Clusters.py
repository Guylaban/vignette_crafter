"""
7_Embedding_Clusters.py — semantic embedding visualization of vignettes.
Projects vignette embeddings to 2D with UMAP, colored by condition.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

st.set_page_config(page_title="Vignette Embeddings", layout="wide")
st.title("Vignette Semantic Embeddings")

# ── Discover runs ─────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "output"


@st.cache_data
def discover_runs() -> pd.DataFrame:
    rows = []
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("craft_persona"):
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

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.header("Settings")

CONDITION_LABELS = {
    "full":           "Full formulation",
    "no_formulation": "No formulation",
    "zero_shot":      "Zero-shot",
}

EVAL_MODELS = [
    "gpt-5.4", "gpt-5.4-mini", "gpt-4o-mini",
    "claude-sonnet-4-6", "claude-haiku-4-5",
    "gemini-2.5-flash", "deepseek-chat", "deepseek-reasoner",
    "qwen2.5-32b", "qwen3.6-35b",
]

available_models  = sorted(runs["model"].unique())
selected_models   = st.sidebar.multiselect(
    "Models", options=available_models,
    default=[m for m in EVAL_MODELS if m in available_models],
)

persona_range  = st.sidebar.slider("Persona IDs", min_value=1, max_value=500, value=(1, 10))
emb_model      = st.sidebar.selectbox("Embedding model", ["all-MiniLM-L6-v2", "MentalBERT"])
auto_neighbors = st.sidebar.checkbox("Auto-select neighbours", value=True)
umap_neighbors = st.sidebar.slider("UMAP neighbours", min_value=2, max_value=30, value=5,
                                   disabled=auto_neighbors)

# ── Load vignettes ────────────────────────────────────────────────────────────

@st.cache_data
def load_vignettes(models: tuple, pid_min: int, pid_max: int) -> pd.DataFrame:
    rows = []
    for model in models:
        for condition in CONDITION_LABELS:
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
                    if text:
                        rows.append({
                            "persona_id": pid,
                            "model":      model,
                            "condition":  condition,
                            "vignette":   text,
                            "preview":    text[:120] + "…",
                        })
                except Exception:
                    continue
    return pd.DataFrame(rows)


if not selected_models:
    st.info("Select at least one model.")
    st.stop()

df = load_vignettes(tuple(selected_models), persona_range[0], persona_range[1])
st.caption(f"{len(df)} vignettes — {len(selected_models)} models, personas {persona_range[0]}–{persona_range[1]}")

if df.empty:
    st.error("No vignettes found.")
    st.stop()

# ── Embedding models ──────────────────────────────────────────────────────────

@st.cache_resource
def load_minilm():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_resource
def load_mentalbert():
    import os, torch
    from transformers import AutoTokenizer, AutoModel
    from huggingface_hub import get_token
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    token = get_token() or os.environ.get("HF_TOKEN")
    tok = AutoTokenizer.from_pretrained("mental/mental-bert-base-uncased", token=token)
    mdl = AutoModel.from_pretrained("mental/mental-bert-base-uncased", token=token)
    mdl.eval()
    return tok, mdl


def encode_minilm(texts):
    return load_minilm().encode(texts, show_progress_bar=False)


def encode_mentalbert(texts):
    import torch
    tok, mdl = load_mentalbert()
    all_embs, batch_size = [], 8
    for i in range(0, len(texts), batch_size):
        enc = tok(texts[i:i+batch_size], padding=True, truncation=True,
                  max_length=512, return_tensors="pt")
        with torch.no_grad():
            out = mdl(**enc)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        all_embs.append(((out.last_hidden_state * mask).sum(1) / mask.sum(1)).numpy())
    return np.vstack(all_embs)


ENCODERS = {"all-MiniLM-L6-v2": encode_minilm, "MentalBERT": encode_mentalbert}

with st.spinner(f"Loading {emb_model}…"):
    if emb_model == "all-MiniLM-L6-v2": load_minilm()
    if emb_model == "MentalBERT":        load_mentalbert()

# ── Embed + UMAP ──────────────────────────────────────────────────────────────

@st.cache_data
def best_neighbors(texts: tuple, model_name: str) -> int:
    import umap
    from sklearn.manifold import trustworthiness
    embs = ENCODERS[model_name](list(texts))
    n = len(texts)
    candidates = [k for k in [2, 3, 5, 8, 10, 15, 20] if k < n]
    best_n, best_score = candidates[0], -1
    scores = {}
    for k in candidates:
        coords = umap.UMAP(n_components=2, n_neighbors=k,
                           min_dist=0.1, random_state=42).fit_transform(embs)
        t = trustworthiness(embs, coords, n_neighbors=k)
        c = trustworthiness(coords, embs, n_neighbors=k)  # continuity
        combined = (t + c) / 2
        scores[k] = round(combined, 3)
        if combined > best_score:
            best_score, best_n = combined, k
    return best_n, scores


@st.cache_data
def compute_umap(texts: tuple, model_name: str, n_neighbors: int) -> np.ndarray:
    import umap
    embs = ENCODERS[model_name](list(texts))
    reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors,
                        min_dist=0.1, random_state=42)
    return reducer.fit_transform(embs)


conditions = list(CONDITION_LABELS.keys())
cols = st.columns(len(conditions))

for col, condition in zip(cols, conditions):
    cond_df = df[df["condition"] == condition].reset_index(drop=True)
    with col:
        st.subheader(CONDITION_LABELS[condition])
        if cond_df.empty:
            st.info("No data for this condition.")
            continue
        texts = tuple(cond_df["vignette"].tolist())
        with st.spinner("Embedding + UMAP…"):
            if auto_neighbors:
                chosen_n, scores = best_neighbors(texts, emb_model)
                scores_str = ", ".join(f"{k}: {v:.3f}" for k, v in scores.items())
                st.caption(f"Auto neighbours = **{chosen_n}** (scores: {scores_str})")
            else:
                chosen_n = umap_neighbors
            coords = compute_umap(texts, emb_model, chosen_n)

        plot_df = cond_df.copy()
        plot_df["x"] = coords[:, 0]
        plot_df["y"] = coords[:, 1]

        fig = px.scatter(
            plot_df, x="x", y="y",
            color="model",
            hover_data={"persona_id": True, "preview": True, "x": False, "y": False},
            title=CONDITION_LABELS[condition],
            labels={"model": "Model"},
            height=520,
        )
        fig.update_traces(marker=dict(size=10, opacity=0.85))
        fig.update_layout(
            xaxis=dict(showticklabels=False, title=""),
            yaxis=dict(showticklabels=False, title=""),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Vignette inspector ────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Vignette inspector")
pid = st.selectbox("Persona ID", sorted(df["persona_id"].unique()))
for _, row in df[df["persona_id"] == pid].sort_values(["condition", "model"]).iterrows():
    label = f"{CONDITION_LABELS.get(row['condition'], row['condition'])} — {row['model']}"
    with st.expander(label):
        st.write(row["vignette"])
