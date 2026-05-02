"""
2_Experiments.py — browse all past experiment runs and their personas.
"""

import logging
import sys
from pathlib import Path

_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

from utils.loader import get_experiments, get_personas, load_persona

st.set_page_config(page_title="Experiments", layout="wide")
st.title("Experiments")


def _build_persona_table(experiment_dir: Path) -> pd.DataFrame:
    rows = []
    for p in get_personas(experiment_dir):
        try:
            data = load_persona(p["path"])
        except Exception as e:
            logger.warning("Failed to load persona %s: %s", p["path"], e)
            continue

        demo = data.get("demographics", {})
        vs   = data.get("validation_summary", {})
        tu   = data.get("token_usage", {})

        rows.append({
            "Persona ID":       data.get("persona_id", p["persona_id"]),
            "Age":              demo.get("age", ""),
            "Gender":           demo.get("gender", ""),
            "Trauma Type":      demo.get("trauma_type", ""),
            "PCL-5":            demo.get("pcl5", ""),
            "Attempts":         vs.get("attempts", ""),
            "Passed":           "Yes" if vs.get("ultimately_passed") else "No",
            "Input Tokens":     tu.get("input", ""),
            "Output Tokens":    tu.get("output", ""),
            "Total Tokens":     tu.get("total", ""),
            "_path":            str(p["path"]),
            "_persona_id":      p["persona_id"],
        })
    return pd.DataFrame(rows)


experiments = get_experiments()

if not experiments:
    st.info("No experiments found. Run `python main.py` to generate vignettes.")
    st.stop()

selected_pid = st.session_state.get("persona_id")
if selected_pid:
    st.success(
        f"Persona **{selected_pid}** is selected — "
        "navigate to **Persona Crafter** or **Vignette** to view details."
    )

st.markdown(f"Found **{len(experiments)}** experiment(s).")

for exp in experiments:
    with st.expander(f"**{exp['name']}**  —  {exp['timestamp']}", expanded=False):

        personas_meta = get_personas(exp["path"])
        cfg = {}
        models = {}
        if personas_meta:
            try:
                first  = load_persona(personas_meta[0]["path"])
                c      = first.get("config", {})
                cfg    = {
                    "Pipeline":        c.get("pipeline", ""),
                    "Temperature":     c.get("temperature", ""),
                    "Max retries":     c.get("max_retries", ""),
                    "Self-report N":   c.get("self_report_items", ""),
                    "Use formulation": c.get("use_formulation", ""),
                    "Seed":            c.get("seed", ""),
                }
                models = c.get("models", {})
            except Exception:
                pass

        # Config metrics row
        if cfg:
            meta_cols = st.columns(len(cfg))
            for col, (k, v) in zip(meta_cols, cfg.items()):
                col.metric(k, str(v))

        if models:
            with st.expander("Models", expanded=False):
                for role, model in models.items():
                    st.markdown(f"- **{role}**: `{model}`")

        st.markdown("---")

        df = _build_persona_table(exp["path"])
        if df.empty:
            st.warning("No persona data found in this experiment.")
            continue

        display_cols = ["Persona ID", "Age", "Gender", "Trauma Type", "PCL-5",
                        "Attempts", "Passed", "Input Tokens", "Output Tokens", "Total Tokens"]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.markdown("**Select a persona:**")
        btn_cols = st.columns(min(len(df), 8))
        for col, (_, row) in zip(btn_cols, df.iterrows()):
            pid   = row["_persona_id"]
            ppath = row["_path"]
            if col.button(f"Persona {pid}", key=f"sel_{exp['name']}_{pid}"):
                persona_data = load_persona(Path(ppath))
                st.session_state["experiment_path"] = str(exp["path"])
                st.session_state["persona_id"]      = pid
                st.session_state["persona_data"]    = persona_data
                st.success(f"Persona **{pid}** selected.")
