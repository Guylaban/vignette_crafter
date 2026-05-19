"""
8_Vignette_TSNE_Clusters.py — t-SNE of cached vignette embeddings, per condition,
with automatic cluster detection and per-cluster persona-field summaries.

Loads pre-built caches from data/analysis/ (built by analysis/vignette_embedding_analysis.ipynb):
  - all_vignettes.parquet                 (df: persona_id, model, condition, vignette, word_count)
  - tsne_coords_per_condition_mpnet.npz   (2D coords per condition, aligned with df rows of that condition)
  - persona_cognitive_cache.json          (active_nodes per persona)
  - personas_long.csv                     (demographics per persona)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import HDBSCAN, KMeans

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

REPO_ROOT    = Path(__file__).parent.parent.parent
ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"

st.set_page_config(page_title="t-SNE Clusters", layout="wide")
st.title("Vignette t-SNE Clusters")
st.caption(
    "Cached all-mpnet-base-v2 embeddings, projected per condition with t-SNE. "
    "Clusters are detected on the 2D coordinates; the table beside each plot "
    "summarises which persona fields dominate each cluster."
)

# ── Required caches ──────────────────────────────────────────────────────────

REQ_FILES = {
    "df":      ANALYSIS_DIR / "all_vignettes.parquet",
    "tsne":    ANALYSIS_DIR / "tsne_coords_per_condition_mpnet.npz",
    "persona": ANALYSIS_DIR / "persona_cognitive_cache.json",
    "demo":    ANALYSIS_DIR / "personas_long.csv",
}
missing = [str(p) for p in REQ_FILES.values() if not p.exists()]
if missing:
    st.error(
        "Missing required cache files:\n\n"
        + "\n".join(f"- `{m}`" for m in missing)
        + "\n\nRun the embedding + t-SNE cells in "
        "`analysis/vignette_embedding_analysis.ipynb` first."
    )
    st.stop()


@st.cache_data
def load_df() -> pd.DataFrame:
    return pd.read_parquet(REQ_FILES["df"])


@st.cache_data
def load_tsne() -> dict:
    z = np.load(REQ_FILES["tsne"])
    return {k: z[k] for k in z.files}


@st.cache_data
def load_persona_meta() -> dict:
    with open(REQ_FILES["persona"], encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}


@st.cache_data
def load_demo() -> pd.DataFrame:
    cols = ["persona_id", "age", "gender", "ethnicity", "trauma_type",
            "pcl5", "relationship_status", "occupation"]
    return (
        pd.read_csv(REQ_FILES["demo"])[cols]
          .drop_duplicates("persona_id")
          .set_index("persona_id")
    )


df            = load_df()
tsne_coords   = load_tsne()
persona_meta  = load_persona_meta()
demo_df       = load_demo()

CONDITION_LABELS = {
    "full":           "Full formulation",
    "no_formulation": "No formulation",
    "zero_shot":      "Zero-shot",
}

# ── Sidebar controls ─────────────────────────────────────────────────────────

st.sidebar.header("Clustering")
algo = st.sidebar.radio("Algorithm", ["HDBSCAN", "KMeans"], index=0)
if algo == "HDBSCAN":
    cluster_param = st.sidebar.slider(
        "Min cluster size", min_value=10, max_value=500, value=80, step=10,
        help="Lower → more, smaller clusters. Higher → fewer, broader clusters.",
    )
    show_outliers = st.sidebar.checkbox("Show outliers (noise points)", value=True)
else:
    cluster_param = st.sidebar.slider("Number of clusters (k)", 2, 15, 6)
    show_outliers = False  # KMeans has no outlier label

st.sidebar.header("Filter")
all_models = sorted(df["model"].unique())
selected_models = st.sidebar.multiselect(
    "Models", all_models, default=all_models,
    help="Cluster only the selected models' vignettes.",
)

show_samples = st.sidebar.checkbox("Show sample vignettes per cluster", value=False)

# ── Hover content (persona-level, cached) ────────────────────────────────────

def _esc(s):
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


@st.cache_data
def build_persona_hover() -> dict:
    out = {}
    for pid, pm in persona_meta.items():
        if pid in demo_df.index:
            d = demo_df.loc[pid]
            demo_block = (
                f"<b>age:</b> {d['age']}  <b>gender:</b> {_esc(d['gender'])}<br>"
                f"<b>ethnicity:</b> {_esc(d['ethnicity'])}<br>"
                f"<b>trauma:</b> {_esc(d['trauma_type'])}  "
                f"<b>PCL-5:</b> {d['pcl5']}<br>"
                f"<b>status:</b> {_esc(d['relationship_status'])}  "
                f"<b>occupation:</b> {_esc(d['occupation'])}"
            )
        else:
            demo_block = "(demographics missing)"
        nodes = pm.get("active_nodes", []) or []
        out[pid] = (
            f"{demo_block}<br>"
            f"<b>active components:</b> "
            f"{', '.join(_esc(n) for n in nodes) or '(none)'}"
        )
    return out


persona_hover = build_persona_hover()

# ── Helpers ──────────────────────────────────────────────────────────────────

def _summarize_cluster(sub: pd.DataFrame, cluster_id) -> dict:
    n = len(sub)
    if n == 0:
        return {"cluster": cluster_id}
    row = {
        "cluster":    "outliers" if cluster_id == -1 else int(cluster_id),
        "n":          n,
        "n_personas": sub["persona_id"].nunique(),
    }
    # Most common categorical fields with their share
    for col, label in [("trauma_type", "trauma"),
                       ("gender",      "gender"),
                       ("ethnicity",   "ethnicity"),
                       ("model",       "model")]:
        if col in sub.columns:
            vc = sub[col].value_counts()
            if len(vc):
                top = vc.index[0]
                row[f"top_{label}"] = f"{top} ({vc.iloc[0]/n:.0%})"
    # Numeric medians
    if "pcl5" in sub.columns and sub["pcl5"].notna().any():
        row["pcl5_med"] = int(sub["pcl5"].median())
    if "age" in sub.columns and sub["age"].notna().any():
        row["age_med"] = int(sub["age"].median())
    # Most common active-component combination
    if "_active_str" in sub.columns:
        vc = sub["_active_str"].value_counts()
        if len(vc):
            row["top_active_set"] = f"{vc.index[0]} ({vc.iloc[0]/n:.0%})"
    return row


def _palette_for(clusters):
    """Stable color map: outliers gray, rest from a long qualitative palette."""
    palette = (px.colors.qualitative.Set1
               + px.colors.qualitative.Dark24
               + px.colors.qualitative.Bold
               + px.colors.qualitative.Pastel)
    pos = sorted(c for c in clusters if c != -1)
    cmap = {c: palette[i % len(palette)] for i, c in enumerate(pos)}
    cmap[-1] = "#cccccc"
    return cmap


def _fit_clusters(coords: np.ndarray):
    if algo == "HDBSCAN":
        return HDBSCAN(min_cluster_size=int(cluster_param)).fit_predict(coords)
    return KMeans(n_clusters=min(int(cluster_param), len(coords)),
                  random_state=42, n_init=10).fit_predict(coords)


# ── Render: one column per condition ─────────────────────────────────────────

if not selected_models:
    st.warning("Select at least one model in the sidebar.")
    st.stop()

cols = st.columns(3)

cluster_state = {}  # for the optional sample-vignettes section below

for col, cond in zip(cols, CONDITION_LABELS):
    with col:
        st.subheader(CONDITION_LABELS[cond])

        # Rows of df for this condition (aligned with tsne_coords[cond])
        cond_mask_full = (df["condition"] == cond).values
        cond_df = df.loc[cond_mask_full].reset_index(drop=True).copy()
        cond_coords_full = tsne_coords[cond]

        # Attach demographics + active-nodes string
        cond_df = cond_df.merge(demo_df, left_on="persona_id",
                                right_index=True, how="left")
        cond_df["_active_str"] = cond_df["persona_id"].map(
            lambda pid: ", ".join(persona_meta.get(int(pid), {})
                                                .get("active_nodes", []))
                        or "(none)"
        )

        # Model filter
        keep = cond_df["model"].isin(selected_models).values
        cond_df = cond_df.loc[keep].reset_index(drop=True)
        coords = cond_coords_full[keep]

        if len(cond_df) == 0:
            st.info("No data with current filters.")
            continue

        # Cluster
        labels = _fit_clusters(coords)
        cond_df["_cluster"] = labels

        # Hover text (cluster id included)
        cond_df["_hover"] = [
            f"<b>persona {int(pid)} | {_esc(m)} | {_esc(c)} | "
            f"cluster {('outliers' if cl == -1 else int(cl))}</b><br>"
            + persona_hover.get(int(pid), "(metadata missing)")
            for pid, m, c, cl in zip(cond_df["persona_id"],
                                     cond_df["model"],
                                     cond_df["condition"],
                                     cond_df["_cluster"])
        ]

        # Plot
        unique_clusters = sorted(set(labels))
        cmap = _palette_for(unique_clusters)

        fig = go.Figure()
        for c in unique_clusters:
            if c == -1 and not show_outliers:
                continue
            mask = labels == c
            name = "outliers" if c == -1 else f"cluster {c}"
            fig.add_trace(go.Scattergl(
                x=coords[mask, 0], y=coords[mask, 1],
                mode="markers",
                name=name,
                marker=dict(
                    size=6,
                    color=cmap.get(c, "#888"),
                    opacity=0.35 if c == -1 else 0.85,
                    line=dict(width=0),
                ),
                customdata=cond_df.loc[mask, "_hover"].values.reshape(-1, 1),
                hovertemplate="%{customdata[0]}<extra></extra>",
            ))
        fig.update_layout(
            height=440,
            xaxis=dict(showticklabels=False, title=""),
            yaxis=dict(showticklabels=False, title=""),
            legend=dict(orientation="v", yanchor="top", y=1, x=1.01,
                        font=dict(size=10)),
            margin=dict(l=10, r=10, t=10, b=10),
            hoverlabel=dict(bgcolor="white", font_size=11,
                            namelength=-1, align="left"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Cluster summary table
        rows = []
        for c in unique_clusters:
            if c == -1 and not show_outliers:
                continue
            rows.append(_summarize_cluster(cond_df[cond_df["_cluster"] == c], c))
        summary_df = pd.DataFrame(rows)
        if not summary_df.empty:
            summary_df = summary_df.set_index("cluster")
        st.dataframe(summary_df, use_container_width=True, height=300)

        cluster_state[cond] = cond_df

# ── Optional: sample vignettes per cluster ──────────────────────────────────

if show_samples and cluster_state:
    st.markdown("---")
    st.subheader("Sample vignettes per cluster")
    sample_cond = st.selectbox(
        "Condition",
        list(cluster_state.keys()),
        format_func=lambda c: CONDITION_LABELS[c],
    )
    sample_df = cluster_state[sample_cond]
    cluster_choices = sorted(set(sample_df["_cluster"]))
    pick = st.selectbox(
        "Cluster",
        cluster_choices,
        format_func=lambda c: "outliers" if c == -1 else f"cluster {c}",
    )
    n_show = st.slider("How many examples", 1, 10, 3)
    samp = (sample_df[sample_df["_cluster"] == pick]
              .head(n_show))
    for _, row in samp.iterrows():
        head = (f"persona {row['persona_id']} | {row['model']} | "
                f"trauma: {row.get('trauma_type', 'n/a')} | "
                f"PCL-5: {row.get('pcl5', 'n/a')}")
        with st.expander(head):
            st.write(row.get("vignette", ""))
