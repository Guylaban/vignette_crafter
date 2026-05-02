"""
sidebar.py — shared sidebar widget for selecting an experiment and persona.

Import and call render_sidebar_selector() at the top of any page that needs
a persona context.
"""

import sys
from pathlib import Path

# Ensure streamlit_app/ is importable
_STREAMLIT_APP_DIR = Path(__file__).parent.parent
if str(_STREAMLIT_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_APP_DIR))

import streamlit as st

from utils.loader import get_experiments, get_personas, load_persona


def render_sidebar_selector() -> tuple:
    """
    Render experiment and persona selectors in the sidebar.

    Returns
    -------
    (experiment_dir, persona_data)
        experiment_dir  Path | None
        persona_data    dict | None

    Both are None when no valid selection exists.
    """
    experiments = get_experiments()

    if not experiments:
        st.sidebar.warning("No experiments found. Run a simulation first.")
        return None, None

    # ── Experiment selector ────────────────────────────────────────────────
    exp_names = [e["name"] for e in experiments]

    # Pre-select if session state carries a remembered path
    default_exp_index = 0
    remembered_path = st.session_state.get("experiment_path")
    if remembered_path:
        try:
            default_exp_index = exp_names.index(Path(remembered_path).name)
        except ValueError:
            pass

    selected_exp_name = st.sidebar.selectbox(
        "Experiment",
        options=exp_names,
        index=default_exp_index,
        key="sidebar_experiment_select",
    )
    experiment_dir = next((e["path"] for e in experiments if e["name"] == selected_exp_name), None)
    if experiment_dir is None:
        st.sidebar.warning("Selected experiment not found.")
        return None, None

    # ── Persona selector ───────────────────────────────────────────────────
    personas = get_personas(experiment_dir)

    if not personas:
        st.sidebar.warning("No personas found in this experiment.")
        return experiment_dir, None

    persona_ids = [p["persona_id"] for p in personas]

    default_idx = 0
    remembered_pid = st.session_state.get("persona_id")
    if remembered_pid and str(remembered_pid) in persona_ids:
        default_idx = persona_ids.index(str(remembered_pid))

    selected_persona_id = st.sidebar.selectbox(
        "Persona",
        options=persona_ids,
        index=default_idx,
        format_func=lambda pid: f"Persona {pid}",
        key="sidebar_persona_select",
    )

    persona_path = next((p["path"] for p in personas if p["persona_id"] == selected_persona_id), None)
    if persona_path is None:
        st.sidebar.warning("Selected persona not found.")
        return experiment_dir, None
    persona_data = load_persona(persona_path)

    # Persist selection in session state so other pages can see it
    st.session_state["experiment_path"] = str(experiment_dir)
    st.session_state["persona_id"]      = selected_persona_id
    st.session_state["persona_data"]    = persona_data

    return experiment_dir, persona_data
