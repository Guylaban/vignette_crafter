import sys
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.vignettes import load_vignettes
from utils.sheets import append_rating, get_completed_vignette_ids, save_demographics, get_demographics

st.set_page_config(page_title="Rate Vignettes", layout="centered", initial_sidebar_state="collapsed")

# ── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 17px; }

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
div[data-testid="stRadio"] input[type="radio"] { display: none; }
div[data-testid="stRadio"] > label { display: none; }

.step-bar { display: flex; gap: 8px; margin-bottom: 4px; }
.step-pill { padding: 5px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
.step-active   { background: #28a745; color: white; }
.step-done     { background: #c3e6cb; color: #155724; }
.step-upcoming { background: #f0f0f0; color: #aaa; }

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

# ── Rater pool assignment ─────────────────────────────────────────────────────
# Each named rater receives a unique, non-overlapping subset of the 300 vignettes.
# Vignettes are sorted by vignette_id (V001–V300) then assigned round-robin so
# every rater's pool is balanced across models and conditions.

RATERS = ["Amit", "Guy", "Nimrod"]


def assign_pool(rater_id: str, all_vignettes: list) -> list:
    if rater_id not in RATERS:
        return sorted(all_vignettes, key=lambda v: v["vignette_id"])
    sorted_v = sorted(all_vignettes, key=lambda v: v["vignette_id"])
    idx = RATERS.index(rater_id)
    return [v for i, v in enumerate(sorted_v) if i % len(RATERS) == idx]


# ── Session state ─────────────────────────────────────────────────────────────

def _init():
    for k, v in [
        ("rater_id", None), ("vignettes", []),
        ("current_idx", 0), ("step", 1), ("current_ratings", {}),
        ("demographics_done", False),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Helpers ───────────────────────────────────────────────────────────────────

def autosave():
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
    labels = ["Read", "Content Validity", "Construction", "DSM-5", "E&C Model"]
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

if not st.session_state.rater_id:
    st.title("Rate Vignettes")
    st.markdown("Select your name to begin or resume your session.")
    rater_id = st.selectbox("Who are you?", [""] + RATERS)
    if st.button("Start", type="primary") and rater_id:
        with st.spinner("Loading..."):
            try:
                all_vignettes = load_vignettes()
            except FileNotFoundError as e:
                st.error(str(e)); st.stop()
            pool = assign_pool(rater_id, all_vignettes)
            rng = random.Random(rater_id)
            rng.shuffle(pool)
            try:
                done_ids = get_completed_vignette_ids(rater_id)
            except Exception:
                done_ids = set()
            start_idx = next(
                (i for i, v in enumerate(pool) if v["vignette_id"] not in done_ids),
                len(pool)
            )
            try:
                demo_done = get_demographics(rater_id) is not None
            except Exception:
                demo_done = False
        st.session_state.update({
            "rater_id": rater_id, "vignettes": pool,
            "current_idx": start_idx, "step": 1, "current_ratings": {},
            "demographics_done": demo_done,
        })
        st.rerun()
    st.stop()

# ── Demographics (one-time, before first vignette) ────────────────────────────

if not st.session_state.demographics_done:
    st.title("Before you begin")
    st.markdown("Please complete this short background questionnaire. Your answers will only be used to describe the sample of raters in the study.")
    st.markdown("---")

    with st.form("demographics_form"):
        st.markdown("#### Professional background")

        title = st.selectbox(
            "Practice degree / professional title *",
            ["", "Clinical Psychologist", "Psychiatrist", "Psychotherapist",
             "Social Worker", "Counselor / MFT", "Psychiatric Nurse",
             "Researcher (non-clinical)", "Other"],
        )
        title_other = ""
        if title == "Other":
            title_other = st.text_input("Please specify your title")

        sex = st.selectbox(
            "Sex *",
            ["", "Male", "Female", "Non-binary / third gender", "Prefer not to say"],
        )

        years = st.number_input(
            "Years in clinical practice *",
            min_value=0, max_value=60, step=1, value=None,
            placeholder="e.g. 12",
        )

        work_status = st.selectbox(
            "Work status *",
            ["", "Full-time clinical practice", "Part-time clinical practice",
             "Combined clinical & academic / research",
             "Primarily academic / research", "Retired", "Other"],
        )

        specialty = st.selectbox(
            "Clinical specialty *",
            ["", "PTSD / Trauma", "Anxiety disorders", "Depression / mood disorders",
             "General adult mental health", "Child / adolescent",
             "Neuropsychology", "Forensic", "Other"],
        )
        specialty_other = ""
        if specialty == "Other":
            specialty_other = st.text_input("Please specify your specialty")

        degree = st.selectbox(
            "Highest academic degree *",
            ["", "BA / BS", "MA / MS", "MSW", "PhD", "PsyD", "MD / MBBCh", "Other"],
        )

        licensure = st.text_input(
            "Current licensure (e.g. Licensed Clinical Psychologist, Board-certified Psychiatrist) *",
            placeholder="Enter your licensure / registration status",
        )

        english = st.selectbox(
            "English speaking and reading proficiency *",
            ["", "Native speaker", "Fluent (bilingual or near-native)",
             "Proficient (professional level)", "Basic"],
        )

        country = st.text_input(
            "Country of current practice *",
            placeholder="e.g. Israel",
        )

        submitted = st.form_submit_button("Continue to rating →", type="primary")

    if submitted:
        required = [title, sex, work_status, specialty, degree, licensure, english, country]
        if any(v == "" or v is None for v in required) or years is None:
            st.warning("Please complete all required fields before continuing.")
        else:
            demo_row = {
                "rater_id":        st.session_state.rater_id,
                "timestamp":       datetime.now(TZ).isoformat(),
                "title":           title if title != "Other" else title_other,
                "sex":             sex,
                "years_practice":  int(years),
                "work_status":     work_status,
                "specialty":       specialty if specialty != "Other" else specialty_other,
                "degree":          degree,
                "licensure":       licensure,
                "english":         english,
                "country":         country,
            }
            try:
                save_demographics(demo_row)
                st.session_state.demographics_done = True
                st.rerun()
            except Exception as e:
                st.error(f"Could not save: {e}")
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
                      "demographics_done",
                      "cvi_clarity", "cvi_relevance", "cvi_representativeness",
                      "evans_g1", "evans_g2", "evans_g3", "evans_g4",
                      "dsm_a", "dsm_b", "dsm_c", "dsm_d", "dsm_e", "dsm_g",
                      "ec_threat", "ec_appraisals", "ec_memory", "ec_strategies", "ec_triggers"]:
                st.session_state.pop(k, None)
            st.rerun()

st.markdown(f"**Completed: {idx} / {total}**")
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
        ("dsm_a", "Traumatic event exposure described"),
        ("dsm_b", "Intrusion symptoms (flashbacks, nightmares, distress at cues)"),
        ("dsm_c", "Avoidance (internal thoughts or external reminders)"),
        ("dsm_d", "Negative cognitions/mood (guilt, shame, detachment, numbing, negative beliefs)"),
        ("dsm_e", "Hyperarousal/reactivity (hypervigilance, startle, sleep, irritability)"),
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
            for k, v in dsm_results.items():
                if v is not None:
                    st.session_state.current_ratings[k] = v
            st.session_state.step = 3
            st.rerun()
    with col_submit:
        if st.button("Next →", type="primary", use_container_width=True):
            if None in dsm_results.values():
                st.session_state["_warn4"] = True
            else:
                st.session_state.pop("_warn4", None)
                for k, v in dsm_results.items():
                    st.session_state.current_ratings[k] = v
                st.session_state.step = 5
                st.rerun()
if st.session_state.pop("_warn4", False):
    st.warning("Please answer all questions before continuing.")

# ── Step 5 — Ehlers & Clark Model ────────────────────────────────────────────

elif step == 5:
    st.markdown("### Ehlers & Clark Model Components")
    st.caption("Is each component present in the vignette?")
    with st.expander("Re-read vignette"):
        st.markdown(f'<div class="vignette-box">{vignette["vignette"]}</div>', unsafe_allow_html=True)
    st.markdown("---")

    EC = [
        ("ec_threat",    "Sense of current threat",
         "The person feels the trauma is still happening or still dangerous right now — not just a bad memory. "
         "E.g. \"The world is unsafe,\" \"I am permanently damaged.\""),
        ("ec_appraisals","Negative appraisals",
         "The person interprets the trauma or its aftermath in an overly negative way. "
         "E.g. \"I caused it,\" \"My flashbacks mean I'm going mad.\""),
        ("ec_memory",    "Nature of trauma memory",
         "The memory is fragmented, disorganised, and feels like it's happening now rather than in the past."),
        ("ec_strategies","Maladaptive strategies",
         "Things the person does to cope that actually keep the PTSD going. "
         "E.g. avoiding reminders, suppressing thoughts, staying busy, drinking, giving up activities they used to enjoy."),
        ("ec_triggers",  "Triggers for re-experiencing",
         "Specific cues — internal or external — that set off flashbacks or distress. "
         "Often not obviously linked to the trauma (e.g. a particular light, a tone of voice, a body position)."),
    ]

    ec_results = {}
    cr = st.session_state.current_ratings
    for key, title, description in EC:
        st.markdown(f"**{title}**")
        st.caption(description)
        ec_results[key] = yn_radio(key, saved=cr.get(key))
        st.markdown("---")

    col_back, _, col_submit = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back"):
            for k, v in ec_results.items():
                if v is not None:
                    st.session_state.current_ratings[k] = v
            st.session_state.step = 4
            st.rerun()
    with col_submit:
        if st.button("Submit", type="primary", use_container_width=True):
            if None in ec_results.values():
                st.session_state["_warn5"] = True
            else:
                st.session_state.pop("_warn5", None)
                dsm_vals   = {k: v for k, v in st.session_state.current_ratings.items() if k.startswith("dsm_")}
                dsm_binary = {k: (1 if v == "Yes" else 0) for k, v in dsm_vals.items() if k != "dsm_valid"}
                dsm_valid  = int(all(dsm_binary.values()))
                ec_binary  = {k: (1 if v == "Yes" else 0) for k, v in ec_results.items()}
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
                    **ec_binary,
                }
                with st.spinner("Saving..."):
                    try:
                        append_rating(row)
                    except Exception as e:
                        st.error(f"Could not save: {e}"); st.stop()

                for k in ["cvi_clarity","cvi_relevance","cvi_representativeness",
                          "evans_g1","evans_g2","evans_g3","evans_g4",
                          "dsm_a","dsm_b","dsm_c","dsm_d","dsm_e","dsm_g",
                          "ec_threat","ec_appraisals","ec_memory","ec_strategies","ec_triggers"]:
                    st.session_state.pop(k, None)

                st.session_state.current_idx    += 1
                st.session_state.step            = 1
                st.session_state.current_ratings = {}
                st.rerun()
if st.session_state.pop("_warn5", False):
    st.warning("Please answer all questions before submitting.")
