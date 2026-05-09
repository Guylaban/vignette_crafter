import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="PTSD Vignette Rating Study",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("PTSD Vignette Rating Study")
st.markdown("---")

st.markdown(
    """
    Welcome. This study asks expert clinicians to evaluate short clinical vignettes
    describing individuals with PTSD.

    **What you will do:**
    - Read one vignette at a time
    - Rate it on three sets of criteria (takes approximately 3–5 minutes per vignette)
    - Your progress is saved automatically — you can close the browser and return later

    **Three rating pages per vignette:**

    1. **Content Validity** — Clarity, Relevance, Representativeness (1–3 scale)
    2. **Construction Quality** — Four clinical vignette guidelines (1–3 scale)
    3. **Diagnostic Validity** — DSM-5 PTSD criteria checklist (Yes / No)

    ---

    **To begin**, navigate to **Rate Vignettes** in the sidebar and enter your rater ID.

    If you do not have a rater ID, please contact the study coordinator.
    """
)

st.info("Use the sidebar on the left to navigate to the rating page.")
