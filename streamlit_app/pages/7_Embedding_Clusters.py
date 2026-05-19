"""
7_Embedding_Clusters.py — semantic embedding visualization of vignettes.
Projects vignette embeddings to 2D with t-SNE, one panel per condition.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

st.set_page_config(page_title="Vignette Embeddings", layout="wide")
st.title("Vignette Semantic Embeddings")

# ── Discover runs ─────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "output"


CONDITION_DIRS = {"full", "no_formulation", "zero_shot"}


@st.cache_data
def discover_runs() -> pd.DataFrame:
    rows = []
    for cond_dir in sorted(OUTPUT_DIR.iterdir()):
        if not cond_dir.is_dir() or cond_dir.name not in CONDITION_DIRS:
            continue
        for model_dir in sorted(cond_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            files = list(model_dir.glob("experiment_*.json"))
            if not files:
                continue
            rows.append({
                "dir":       model_dir,
                "model":     model_dir.name,
                "condition": cond_dir.name,
                "n":         len(files),
            })
    return pd.DataFrame(rows)


runs = discover_runs()
if runs.empty:
    st.error(
        f"No vignette runs found under `{OUTPUT_DIR}`. Expected layout: "
        "`data/output/{full,no_formulation,zero_shot}/<model>/experiment_*.json`."
    )
    st.stop()

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

available_models = sorted(runs["model"].unique())
preferred_first = next((m for m in EVAL_MODELS if m in available_models),
                       available_models[0])
selected_model = st.sidebar.selectbox(
    "Model", options=available_models,
    index=available_models.index(preferred_first),
)

PID_MIN, PID_MAX = 1, 500
emb_model = "all-MiniLM-L6-v2"

HIGHLIGHT_PALETTE = [
    "#EF6769",  # red
    "#5D89D0",  # blue
    "#80CB7D",  # green
    "#984EA3",  # purple
    "#FFB96E",  # orange
    "#F781BF",  # pink
    "#65C3BD",  # teal
]
GRAY = "#bdbaba"

# ── Load vignettes ────────────────────────────────────────────────────────────

def _esc(s):
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def _build_hover(pid, demo, active_nodes):
    age = demo.get("age", "?")
    gender = _esc(demo.get("gender", "?"))
    ethnicity = _esc(demo.get("ethnicity", "?"))
    trauma = _esc(demo.get("trauma_type", "?"))
    pcl5 = demo.get("pcl5", "?")
    status = _esc(demo.get("relationship_status", "?"))
    occ = _esc(demo.get("occupation", "?"))
    nodes = ", ".join(_esc(n) for n in (active_nodes or [])) or "(none)"
    return (
        f"<b>persona {pid}</b><br>"
        f"<b>age:</b> {age}  <b>gender:</b> {gender}<br>"
        f"<b>ethnicity:</b> {ethnicity}<br>"
        f"<b>trauma:</b> {trauma}  <b>PCL-5:</b> {pcl5}<br>"
        f"<b>status:</b> {status}  <b>occupation:</b> {occ}<br>"
        f"<b>active components:</b> {nodes}"
    )


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
                        demo = data.get("demographics", {}) or {}
                        active_nodes = data.get("active_nodes", []) or []
                        rows.append({
                            "persona_id":  pid,
                            "model":       model,
                            "condition":   condition,
                            "vignette":    text,
                            "trauma_type": demo.get("trauma_type") or "Unknown",
                            "hover":       _build_hover(pid, demo, active_nodes),
                        })
                except Exception:
                    continue
    return pd.DataFrame(rows)


df = load_vignettes((selected_model,), PID_MIN, PID_MAX)
st.caption(f"{len(df)} vignettes — {selected_model} × 500 personas × 3 conditions")

if df.empty:
    st.error("No vignettes found.")
    st.stop()

all_trauma_types = sorted(t for t in df["trauma_type"].dropna().unique())
highlighted_traumas = st.sidebar.multiselect(
    "Highlight trauma types",
    options=all_trauma_types,
    default=[],
    help="Pick one or more trauma types to color. Others are shown in gray. "
         "Leave empty to color everything.",
)

# ── Embedding models ──────────────────────────────────────────────────────────

@st.cache_resource
def load_minilm():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def encode_minilm(texts):
    return load_minilm().encode(texts, show_progress_bar=False)


ENCODERS = {"all-MiniLM-L6-v2": encode_minilm}

with st.spinner(f"Loading {emb_model}…"):
    load_minilm()

# ── Embed + t-SNE ────────────────────────────────────────────────────────────

def _auto_perplexity(n: int) -> int:
    """sqrt(N) heuristic, clamped to [5, 50] and to t-SNE's hard limit (n-1)/3."""
    import math
    p = int(round(math.sqrt(max(n, 1))))
    p = max(5, min(50, p))
    return max(2, min(p, (n - 1) // 3))


@st.cache_data
def compute_tsne(texts: tuple, model_name: str):
    from sklearn.manifold import TSNE
    embs = ENCODERS[model_name](list(texts))
    n = len(embs)
    p = _auto_perplexity(n)
    reducer = TSNE(n_components=2, perplexity=p,
                   learning_rate="auto", init="pca", random_state=42)
    return reducer.fit_transform(embs), p


conditions = list(CONDITION_LABELS.keys())

cond_coords = {}
cond_plot_df = {}
cond_perp = {}
skipped = {}
for condition in conditions:
    cond_df = df[df["condition"] == condition].reset_index(drop=True)
    if cond_df.empty:
        skipped[condition] = "No data for this condition."
        continue
    texts = tuple(cond_df["vignette"].tolist())
    if len(texts) < 6:
        skipped[condition] = (
            f"Only {len(texts)} vignette(s) in this slice — need at least 6 "
            "for t-SNE. Add more models."
        )
        continue
    with st.spinner(f"Embedding + t-SNE ({CONDITION_LABELS[condition]})…"):
        coords, chosen_p = compute_tsne(texts, emb_model)
    plot_df = cond_df.copy()
    plot_df["x"] = coords[:, 0]
    plot_df["y"] = coords[:, 1]
    cond_coords[condition] = coords
    cond_plot_df[condition] = plot_df
    cond_perp[condition] = chosen_p

if cond_plot_df:
    trauma_order = sorted(
        {t for pdf in cond_plot_df.values() for t in pdf["trauma_type"].dropna().unique()}
    )
    if highlighted_traumas:
        trauma_color = {t: HIGHLIGHT_PALETTE[i % len(HIGHLIGHT_PALETTE)]
                        for i, t in enumerate(highlighted_traumas)}
    else:
        TRAUMA_PALETTE = (
            px.colors.qualitative.Plotly
            + px.colors.qualitative.Set3
            + px.colors.qualitative.Pastel
        )
        trauma_color = {t: TRAUMA_PALETTE[i % len(TRAUMA_PALETTE)]
                        for i, t in enumerate(trauma_order)}

    fig = make_subplots(
        rows=1, cols=len(conditions),
        subplot_titles=[CONDITION_LABELS[c] for c in conditions],
        horizontal_spacing=0.05,
    )

    seen_in_legend = set()
    other_label = f"Other ({len(trauma_order) - len(highlighted_traumas)} trauma types)"
    for col_idx, condition in enumerate(conditions, start=1):
        plot_df = cond_plot_df.get(condition)
        if plot_df is None:
            continue

        if highlighted_traumas:
            bg_mask = (~plot_df["trauma_type"].isin(highlighted_traumas)).values
            if bg_mask.any():
                bg = plot_df.loc[bg_mask]
                show_bg_legend = "__other__" not in seen_in_legend
                seen_in_legend.add("__other__")
                fig.add_trace(
                    go.Scattergl(
                        x=bg["x"].values, y=bg["y"].values,
                        mode="markers",
                        name=other_label,
                        legendgroup="__other__",
                        showlegend=show_bg_legend,
                        marker=dict(size=5, color=GRAY, opacity=0.35,
                                    line=dict(width=0)),
                        customdata=bg["hover"].values.reshape(-1, 1),
                        hovertemplate="%{customdata[0]}<extra></extra>",
                    ),
                    row=1, col=col_idx,
                )
            iter_traumas = [t for t in highlighted_traumas if t in trauma_order]
            marker_size = 10
        else:
            iter_traumas = trauma_order
            marker_size = 7

        for t in iter_traumas:
            t_mask = (plot_df["trauma_type"] == t).values
            if not t_mask.any():
                continue
            show_in_legend = t not in seen_in_legend
            seen_in_legend.add(t)
            sub = plot_df.loc[t_mask]
            fig.add_trace(
                go.Scattergl(
                    x=sub["x"].values, y=sub["y"].values,
                    mode="markers",
                    name=t,
                    legendgroup=t,
                    showlegend=show_in_legend,
                    marker=dict(size=marker_size, color=trauma_color[t],
                                opacity=0.9,
                                line=dict(width=0.4, color="white")),
                    customdata=sub["hover"].values.reshape(-1, 1),
                    hovertemplate="%{customdata[0]}<extra></extra>",
                ),
                row=1, col=col_idx,
            )

    for i in range(1, len(conditions) + 1):
        fig.update_xaxes(showticklabels=False, title_text="", row=1, col=i)
        fig.update_yaxes(showticklabels=False, title_text="", row=1, col=i)

    fig.update_layout(
        height=560,
        legend=dict(title="Trauma type", itemsizing="constant",
                    yanchor="top", y=1, x=1.02, font=dict(size=10)),
        hoverlabel=dict(bgcolor="white", font_size=11, namelength=-1, align="left"),
        margin=dict(l=10, r=220, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    perp_caption = " · ".join(
        f"{CONDITION_LABELS[c]}: perplexity **{cond_perp[c]}** "
        f"(~√N on {len(cond_plot_df[c])} points)"
        for c in conditions if c in cond_perp
    )
    if perp_caption:
        st.caption(perp_caption)

for condition, msg in skipped.items():
    st.info(f"**{CONDITION_LABELS[condition]}** {msg}")
