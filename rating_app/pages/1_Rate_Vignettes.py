import sys
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.vignettes import load_vignettes
from utils.sheets import append_rating, get_completed_vignette_ids

st.set_page_config(page_title="Rate Vignettes", layout="centered", initial_sidebar_state="collapsed")

# ── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 17px; }

/* Radio buttons → pill buttons */
div[data-testid="stRadio"] > div {
    display: flex;
    gap: 10px;
    flex-wrap: nowrap;
    margin-top: 6px;
}
div[data-testid="stRadio"] label {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    border: 2px solid #d0d0d0;
    border-radius: 10px;
    cursor: pointer;
    font-size: 15px;
    background: #fafafa;
    transition: all 0.15s;
    white-space: nowrap;
}
div[data-testid="stRadio"] label:hover {
    border-color: #28a745;
    background: #f0fff4;
}
div[data-testid="stRadio"] label:has(input:checked) {
    border-color: #28a745;
    background: #e8f5e9;
    font-weight: 600;
}
div[data-testid="stRadio"] label span { margin-left: 8px; }

/* Hide default radio circles and empty label */
div[data-testid="stRadio"] input[type="radio"] { display: none; }
div[data-testid="stRadio"] > label { display: none; }

/* Step indicator */
.step-bar { display: flex; gap: 8px; margin-bottom: 4px; }
.step-pill { padding: 5px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
.step-active   { background: #28a745; color: white; }
.step-done     { background: #c3e6cb; color: #155724; }
.step-upcoming { background: #f0f0f0; color: #aaa; }

/* Vignette box */
.vignette-box {
    background: #f8f9fa;
    border-left: 4px solid #28a745;
    padding: 20px 24px;
    border-radius: 6px;
    font-size: 17px;
    line-height: 1.75;
    margin-bottom: 20px;
    color: #212529;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    for k, v in [
        ("rater_id", None), ("vignettes", []),
        ("current_idx", 0), ("step", 1), ("current_ratings", {}),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Helpers ───────────────────────────────────────────────────────────────────

def autosave():
    """Read current widget values into current_ratings so navigation doesn't lose them."""
    step = st.session_state.step
    cr = st.session_state.current_ratings
    if step == 2:
        for wkey, rkey in [("cvi_clarity","clarity"),("cvi_relevance","relevance"),("cvi_representativeness","representativeness")]:
            if st.session_state.get(wkey) is not None:
                cr[rkey] = st.session_state[wkey]
    elif step == 3:
        for wkey, rkey in [("evans_g1","g1_grounded"),("evans_g2","g2_narrative"),("evans_g3","g3_explicit"),("evans_g4","g4_relevant")]:
            if st.session_state.get(wkey) is not None:
                cr[rkey] = st.session_state[wkey]


def step_nav(current: int):
    labels = ["Read", "Content Validity", "Construction", "DSM-5"]
    pills = ""
    for i, label in enumerate(labels, 1):
        if i < current:
            cls = "step-done"
        elif i == current:
            cls = "step-active"
        else:
            cls = "step-upcoming"
        pills += f'<span class="step-pill {cls}">{label}</span>'
    st.markdown(f'<div class="step-bar">{pills}</div>', unsafe_allow_html=True)


def rating_radio(label, key, low, high):
    st.markdown(f"**{label}**")
    saved = st.session_state.current_ratings.get(key)
    idx = [1,2,3].index(saved) if saved in [1,2,3] else None
    return st.radio(
        "", [1, 2, 3],
        format_func=lambda x: {1: f"1 — {low}", 2: "2 — Somewhat", 3: f"3 — {high}"}[x],
        horizontal=True, key=key, index=idx, label_visibility="collapsed",
    )


def yn_radio(key, saved=None):
    idx = ["No","Yes"].index(saved) if saved in ["No","Yes"] else None
    return st.radio(
        "", ["No", "Yes"],
        horizontal=True, key=key, index=idx, label_visibility="hidden",
    )


# ── Login ─────────────────────────────────────────────────────────────────────

RATERS = ["", "Amit", "Guy", "Nimrod"]

if not st.session_state.rater_id:
    st.title("Rate Vignettes")
    st.markdown("Select your name to begin or resume your session.")
    rater_id = st.selectbox("Who are you?", RATERS)
    if st.button("Start", type="primary") and rater_id:
        rid = rater_id
        with st.spinner("Loading..."):
            try:
                all_vignettes = load_vignettes()
            except FileNotFoundError as e:
                st.error(str(e)); st.stop()
            rng = random.Random(rid)
            shuffled = all_vignettes.copy()
            rng.shuffle(shuffled)
            try:
                done_ids = get_completed_vignette_ids(rid)
            except Exception:
                done_ids = set()
            start_idx = next(
                (i for i, v in enumerate(shuffled) if v["vignette_id"] not in done_ids),
                len(shuffled)
            )
        st.session_state.update({
            "rater_id": rid, "vignettes": shuffled,
            "current_idx": start_idx, "step": 1, "current_ratings": {},
        })
        st.rerun()
    st.stop()

# ── All done ──────────────────────────────────────────────────────────────────

vignettes = st.session_state.vignettes
total     = len(vignettes)
idx       = st.session_state.current_idx

if idx >= total:
    st.title("All done!")
    st.success(f"Thank you! You have rated all {total} vignettes. Your responses have been saved.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────

vignette = vignettes[idx]
step     = st.session_state.step

with st.container():
    col_name, col_logout = st.columns([6, 1])
    with col_name:
        st.markdown(f"Logged in as **{st.session_state.rater_id}**")
    with col_logout:
        if st.button("Log out", use_container_width=True):
            for k in ["rater_id", "vignettes", "current_idx", "step", "current_ratings",
                      "cvi_clarity", "cvi_relevance", "cvi_representativeness",
                      "evans_g1", "evans_g2", "evans_g3", "evans_g4",
                      "dsm_a", "dsm_b", "dsm_c", "dsm_d", "dsm_e", "dsm_g"]:
                st.session_state.pop(k, None)
            st.rerun()

st.markdown(f"**Completed: {idx}**")
st.progress(idx / total)
st.markdown("---")
step_nav(step)
st.markdown("---")

# ── Step 1 — Read ─────────────────────────────────────────────────────────────

if step == 1:
    st.markdown("### Read this vignette carefully")
    st.markdown(f'<div class="vignette-box">{vignette["vignette"]}</div>', unsafe_allow_html=True)
    _, col_next = st.columns([4, 1])
    with col_next:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# ── Step 2 — Content Validity ─────────────────────────────────────────────────

elif step == 2:
    st.markdown("### Content Validity")
    st.caption("Rate each dimension. 1 = low, 3 = high.")
    with st.expander("Re-read vignette"):
        st.markdown(f'<div class="vignette-box">{vignette["vignette"]}</div>', unsafe_allow_html=True)
    st.markdown("---")

    cr = st.session_state.current_ratings
    clarity            = rating_radio("Clarity — How clearly is the vignette written?",           "cvi_clarity",            "Unclear",            "Very clear")
    st.markdown("")
    relevance          = rating_radio("Relevance — Is this vignette relevant to a PTSD case?",    "cvi_relevance",          "Not relevant",       "Very relevant")
    st.markdown("")
    representativeness = rating_radio("Representativeness — Does this accurately represent PTSD?", "cvi_representativeness", "Not representative", "Very representative")
    st.markdown("---")

    col_back, _, col_next = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            autosave()
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Next →", type="primary", use_container_width=True):
            if None in (clarity, relevance, representativeness):
                st.session_state["_warn2"] = True
            else:
                st.session_state.pop("_warn2", None)
                st.session_state.current_ratings.update({
                    "clarity": clarity, "relevance": relevance,
                    "representativeness": representativeness,
                })
                st.session_state.step = 3
                st.rerun()
if st.session_state.pop("_warn2", False):
    st.warning("Please answer all questions before continuing.")

# ── Step 3 — Construction ─────────────────────────────────────────────────────

elif step == 3:
    st.markdown("### Construction Quality")
    st.caption("Rate how well the vignette meets each guideline. 1 = not at all, 3 = very much.")
    with st.expander("Re-read vignette"):
        st.markdown(f'<div class="vignette-box">{vignette["vignette"]}</div>', unsafe_allow_html=True)
    st.markdown("---")

    g1 = rating_radio("The vignette appears grounded in realistic clinical experience or literature",       "evans_g1", "Not at all", "Very much")
    st.markdown("")
    g2 = rating_radio("The vignette reads as a personal narrative rather than a symptom checklist",        "evans_g2", "Not at all", "Very much")
    st.markdown("")
    g3 = rating_radio("PTSD-relevant details are explicit and identifiable",                               "evans_g3", "Not at all", "Very much")
    st.markdown("")
    g4 = rating_radio("Only relevant clinical information is included; nothing confusing or misleading",   "evans_g4", "Not at all", "Very much")
    st.markdown("---")

    col_back, _, col_next = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            autosave()
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("Next →", type="primary", use_container_width=True):
            if None in (g1, g2, g3, g4):
                st.session_state["_warn3"] = True
            else:
                st.session_state.pop("_warn3", None)
                st.session_state.current_ratings.update({
                    "g1_grounded": g1, "g2_narrative": g2,
                    "g3_explicit": g3, "g4_relevant": g4,
                })
                st.session_state.step = 4
                st.rerun()
if st.session_state.pop("_warn3", False):
    st.warning("Please answer all questions before continuing.")

# ── Step 4 — DSM-5 ───────────────────────────────────────────────────────────

elif step == 4:
    st.markdown("### DSM-5 Validity Check")
    st.caption("Is each criterion present in the vignette?")
    with st.expander("Re-read vignette"):
        st.markdown(f'<div class="vignette-box">{vignette["vignette"]}</div>', unsafe_allow_html=True)
    st.markdown("---")

    DSM = [
        ("dsm_a", "Traumatic event exposure (at least 1 required)"),
        ("dsm_b", "Intrusion symptoms — flashbacks, nightmares, or distress at reminders (at least 1 required)"),
        ("dsm_c", "Avoidance of thoughts or external reminders (at least 1 required)"),
        ("dsm_d", "Negative cognitions or mood — guilt, shame, detachment, numbing, or negative beliefs (at least 2 required)"),
        ("dsm_e", "Hyperarousal or reactivity — hypervigilance, startle, sleep problems, or irritability (at least 2 required)"),
        ("dsm_g", "Functional impairment mentioned"),
    ]

    dsm_results = {}
    cr = st.session_state.current_ratings
    for key, description in DSM:
        st.markdown(f"**{description}**")
        dsm_results[key] = yn_radio(key, saved=cr.get(key))
        st.markdown("---")

    col_back, _, col_submit = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            # save DSM answers so far
            for k, v in dsm_results.items():
                if v is not None:
                    st.session_state.current_ratings[k] = v
            st.session_state.step = 3
            st.rerun()
    with col_submit:
        if st.button("Submit", type="primary", use_container_width=True):
            if None in dsm_results.values():
                st.session_state["_warn4"] = True
            else:
                st.session_state.pop("_warn4", None)
                dsm_binary = {k: (1 if v == "Yes" else 0) for k, v in dsm_results.items()}
                dsm_valid  = int(all(dsm_binary.values()))
                row = {
                    "timestamp":       datetime.now(TZ).isoformat(),
                    "rater_id":        st.session_state.rater_id,
                    "vignette_number": idx + 1,
                    "vignette_id":     vignette["vignette_id"],
                    "persona_id":      vignette["persona_id"],
                    "model":           vignette["model"],
                    "condition":       vignette["condition"],
                    **st.session_state.current_ratings,
                    **dsm_binary,
                    "dsm_valid":       dsm_valid,
                }
                with st.spinner("Saving..."):
                    try:
                        append_rating(row)
                    except Exception as e:
                        st.error(f"Could not save: {e}"); st.stop()

                # clear widget keys for next vignette
                for k in ["cvi_clarity","cvi_relevance","cvi_representativeness",
                          "evans_g1","evans_g2","evans_g3","evans_g4",
                          "dsm_a","dsm_b","dsm_c","dsm_d","dsm_e","dsm_g"]:
                    st.session_state.pop(k, None)

                st.session_state.current_idx    += 1
                st.session_state.step            = 1
                st.session_state.current_ratings = {}
                st.rerun()
if st.session_state.pop("_warn4", False):
    st.warning("Please answer all questions before submitting.")
