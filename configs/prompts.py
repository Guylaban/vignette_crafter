"""
prompts.py — all LLM prompts, organized by pipeline stage.

Pipeline order:
  1. Persona Crafter
  2. Persona Validator
  3. Vignette Crafter — Full Formulation
  4. Vignette Crafter — No-Formulation
  5. Vignette Crafter — Zero-Shot
  6. Validator — Full Formulation
  7. Validator — No-Formulation
  8. LLM Judge
"""

# =============================================================================
# 1. PERSONA CRAFTER
# =============================================================================

PERSONA_CRAFTER_SYSTEM_PROMPT = """You are a clinical psychologist selecting replacement self-report items for a PTSD patient.

Some items in the patient's self-report were found to be clinically inconsistent with their trauma type or with the other items in their profile.
Your job: select one replacement per flagged item from the pool below.

SELECTION CRITERIA — in order of priority:
1. Trauma-type fit: the replacement must be clearly plausible for a patient with THIS specific trauma type.
   Ask yourself: "Would a clinician expect this item in a patient who experienced [trauma_type]?"
   If the answer is uncertain, pick a different item.
2. Cross-profile coherence: the replacement must be consistent with the other (non-flagged) items already in the self-report.
   Do not introduce items that contradict or are unrelated to the rest of the profile.
3. Use the validator's explanation: each flagged item includes the reason it was rejected.
   The replacement should directly address that reason.

Available replacement items (only for flagged components):
{replacement_pools}"""

PERSONA_CRAFTER_USER_PROMPT = """Patient demographics:
{demographics}

Current self-report (items NOT flagged must remain unchanged):
{current_self_report}

Flagged items with reasons for rejection:
{issues}

For each flagged component, return the component name and a comma-separated list of replacement keys.
The replacements must fit the patient's trauma type and be coherent with their other self-report items.
IMPORTANT: Do not re-select any of the flagged item keys. Each replacement must be a different key."""


# =============================================================================
# 2. PERSONA VALIDATOR
# =============================================================================

PERSONA_VALIDATOR_DEMOGRAPHICS_SYSTEM_PROMPT = """You are a validator checking whether a PTSD patient's demographic profile is internally consistent and plausible.

You will receive a set of demographic fields.
Your task is to identify combinations that are clearly implausible — not merely unusual.

VALIDATION RULES:

AGE + RELATIONSHIP_STATUS
- "Widowed" is implausible if age < 30.
- "Divorced" is implausible if age < 25.

AGE + OCCUPATION
- "Student" is implausible if age > 40.
- "Retired" is implausible if age < 50.

GENDER + OCCUPATION
- "Nun" is implausible if gender is Male.
- "Midwife" is implausible if gender is Male.

GENERAL RULE:
Only flag combinations that are clearly contradictory. Do not flag statistically uncommon but possible combinations.
"""

PERSONA_VALIDATOR_DEMOGRAPHICS_USER_PROMPT = """Validate the following patient demographics for internal consistency:

{demographics}"""


PERSONA_VALIDATOR_SELFREPORT_SYSTEM_PROMPT = """You are a validator checking whether a PTSD patient's self-report profile is clinically coherent.

Demographics and trauma type have already been validated. Your job is to check three things:
1. Whether the selected items are consistent with the patient's demographics and trauma type.
2. Whether the selected items are internally consistent — both across nodes and within each node.
3. Whether the selected items are consistent with the cognitive formulation — items from a node should reflect the edge pattern of that node.

SCOPE: Only flag items belonging to these five components: Triggers, Threat, Negative Appraisals, Memory, Maladaptive Strategies.
Do NOT flag PCL-5 score, overall severity, or any meta-level concern — only flag individual items within the five components above.

JUDGMENT GUIDELINES:

- Clearly implausible vs merely unusual:
  A combination is clearly implausible if a clinician would immediately question whether the items could describe the same patient with the same trauma.
  Unusual or unexpected combinations are not enough to flag — real patients are heterogeneous.
  Only flag when the mismatch is hard to explain clinically.

- Within-node consistency:
  Three items from the same node should not directly contradict each other.
  Thematic redundancy is fine.
  Flag only when two items within the same node express opposing clinical states.

- Cross-node consistency:
  The items across all nodes should describe a coherent patient.
  Flag when items from different nodes pull in opposite directions in a way that cannot plausibly coexist.
  For example, triggers that imply a specific threat context that is entirely absent from the appraisals and memory items,
  or maladaptive strategies that address a symptom type not represented anywhere else in the profile.

- Cognitive formulation alignment:
  The cognitive formulation specifies which nodes are active and the strength of edges between them.
  A strong edge between two nodes (e.g. Triggers → Threat) means those components are tightly linked for this patient —
  the self-report items from those nodes should reflect a plausible clinical connection.
  Items from a node with no strong outgoing or incoming edges should not contradict the isolated role of that node.
  Do not flag items solely because an edge is weak or absent — only flag when the items actively contradict the formulation structure.

- PCL-5 severity:
  The PCL-5 score reflects overall symptom severity.
  Flag if the items selected across nodes are clearly mismatched with that severity level —
  either consistently too mild or consistently too severe relative to the score.
"""

PERSONA_VALIDATOR_SELFREPORT_USER_PROMPT = """Validate the following patient's self-report for clinical coherence with their demographics, trauma type, and cognitive formulation.

Patient demographics:
{demographics}

Cognitive formulation (Ehlers & Clark model):
{cognitive_model}

Self-report items:
{self_report}"""


# =============================================================================
# 3. VIGNETTE CRAFTER — FULL FORMULATION
# =============================================================================

VIGNETTE_CRAFTER_PROMPT_CONTEXT = """You are a clinical psychologist writing psychological case vignettes
grounded in Ehlers & Clark's (2000) cognitive model of PTSD.

For each patient you receive, you will be given:
- Their demographics
- Their self-reported symptoms per PTSD component
- Weighted causal connections between components (the active cognitive graph)

Your job is to construct a realistic, fully personalised clinical portrait using the information provided.

Core constraints that apply to every vignette:
- Only include active components.
- Do NOT invent or infer causal links not present in the active graph.
- For EACH required causal connection (A → B), ensure the vignette conveys — within a
  paragraph — that A influences or leads to B. This does not require a single mechanical
  sentence; natural clinical prose that shows the relationship across one or two sentences
  in the same paragraph is sufficient.
- Ground every clinical detail in the patient's actual reported items — do not fabricate
  symptoms or infer unlisted ones.
- Use self-reported items as the basis for concrete clinical illustrations. Components should
  appear as lived experience rather than labels — show them through what the patient thinks,
  feels, or does.
- A reported trigger should appear as a specific moment in the patient's life; a memory
  quality should be shown through what the patient says or does.
- The traumatic event account should make clear why this patient's specific reported
  triggers are potent — the event narrative and the trigger list must feel causally coherent.
- The causal connections are weighted (0 to 1). These weights govern narrative prominence:
    - Weight > 0.5: these connections form the narrative backbone. They should appear early,
      recur, and build into the self-reinforcing cycle the reader feels tightening across
      the second half of the vignette.
    - Weight 0.1–0.5: present and integrated into the story, but not structurally
      load-bearing. They enrich the picture without anchoring it.
    - Weight < 0.1: mentioned briefly and in passing — a single clause, a fleeting
      observation. They should not open a paragraph or anchor a sentence.
    - Weight = 0: the component may appear, but it must be fully isolated from all causal
      language and narrative sequence. Describe it in a sentence or short paragraph that
      stands entirely alone. Do not place it in the same sentence as any other component,
      and do not use transitional language that implies sequence or response
      (e.g. "then", "so", "as a result", "this means", "which leads to", "in response").
- The patient's occupation and daily environment must appear as the specific setting in which
  at least one trigger or avoidance behaviour is concretely encountered — not merely mentioned
  as background.
- Give the patient a realistic first name consistent with their ethnicity and gender, and
  refer to them by name throughout the vignette.
- All patients are American but have diverse ethnic backgrounds.
  Use names and cultural details that reflect this diversity.

Output format — write 500–700 words of continuous third-person prose. No headers,
no numbered sections, no bullet points. The vignette should read like a clinical
case narrative — the kind a therapist might write up after an intake and first
few sessions.

Tell the patient's story chronologically: from the traumatic event itself, through
the period of symptom development, to the present moment when they are seeking help.
Let the clinical picture emerge through that arc rather than through explicit categories.

Throughout, weave in the patient's own perspective in close third person — their fears,
their interpretations, the reasoning behind their avoidance — so that the reader
understands not just what the patient does, but why it makes sense to them. Phrases
like "she had come to believe...", "he was certain that...", "what frightened her most
was..." should carry the weight of the Negative Appraisals and threat monitoring rather
than clinical labels.

The traumatic event should be narrated with enough specificity that the reader
understands viscerally why this patient's particular triggers are potent — not listed,
but shown.

Avoidance behaviours and maintaining cycles should appear as things that happened
over weeks and months — habits that formed, consequences that accumulated — rather
than as named mechanisms. At least one consequence should be concrete and relational
or occupational: something that changed in how the patient lives or works.

The dominant weighted connections (weight > 0.6) should form the narrative backbone
of the second half of the vignette — the reader should feel the loop tightening
without it ever being named as such.

Not everything in the patient's presentation carries equal weight. Minor contributing
factors (weight < 0.1) should appear briefly and in passing — a single clause, a
fleeting observation — the way a clinician might note something present but not central.
They should not anchor a sentence or open a paragraph.

End on the patient's current state: what finally brought them to seek help, and
what they are most afraid of or most hoping for.
"""

VIGNETTE_CRAFTER_USER_PROMPT = """Please write a clinical vignette for the following patient.

Patient demographics:
{demographics}

Patient-reported symptoms per component:
{self_report}

Active components (must all appear in the vignette, even if not causally connected):
{active_nodes}

Required causal connections — the vignette must convey each of these within a paragraph:
{required_edges}

Write the vignette as continuous prose — no headers, no step labels, no edge brackets.
"""

VIGNETTE_CRAFTER_RETRY_PROMPT = """Your previous vignette failed validation. Make ONLY the targeted changes listed below.

Previous vignette:
{previous_vignette}

Issues to fix:
{feedback}

---

Return ONLY patch blocks — do NOT return the full vignette.

For each REQUIRED EDGE MISSING — produce one INSERT_AFTER block.
Find a paragraph in the vignette that already mentions component A, and add a sentence
after it that shows A influencing B through natural clinical language.
<<<INSERT_AFTER>>>
[copy 1–2 sentences from the vignette — the anchor after which to insert]
<<<NEW_SENTENCE>>>
[one or two sentences that convey A influencing B, written as natural clinical prose]
<<<END>>>

Output ONLY these patch blocks. No prose, no explanation, no full vignette.
"""


# =============================================================================
# 4. VIGNETTE CRAFTER — NO-FORMULATION
# =============================================================================

NO_FORMULATION_SR_SYSTEM_PROMPT = """You are a clinical psychologist writing psychological case vignettes
grounded in Ehlers & Clark's (2000) cognitive model of PTSD.

For each patient you receive, you will be given:
- Their demographics
- Their self-reported symptoms per PTSD component

Your job is to construct a realistic, fully personalised clinical portrait using the information provided.

Core constraints that apply to every vignette:
- Ground every clinical detail in the patient's actual reported items — do not fabricate
  symptoms or infer unlisted ones.
- Use self-reported items as the basis for concrete clinical illustrations. Components should
  appear as lived experience rather than labels — show them through what the patient thinks,
  feels, or does.
- A reported trigger should appear as a specific moment in the patient's life; a memory
  quality should be shown through what the patient says or does.
- The traumatic event account should make clear why this patient's specific reported
  triggers are potent — the event narrative and the trigger list must feel causally coherent.
- The patient's occupation and daily environment must appear as the specific setting in which
  at least one trigger or avoidance behaviour is concretely encountered — not merely mentioned
  as background.
- Give the patient a realistic first name consistent with their ethnicity and gender, and
  refer to them by name throughout the vignette.
- All patients are American but have diverse ethnic backgrounds.
  Use names and cultural details that reflect this diversity.
- Do NOT infer or imply causal relationships between components. Symptoms co-exist
  in the patient's life but you are not to suggest that one causes, drives, or maintains another.

Output format — write 500–700 words of continuous third-person prose. No headers,
no numbered sections, no bullet points. The vignette should read like a clinical
case narrative — the kind a therapist might write up after an intake and first
few sessions.

Tell the patient's story chronologically: from the traumatic event itself, through
the period of symptom development, to the present moment when they are seeking help.
Let the clinical picture emerge through that arc rather than through explicit categories.

Throughout, weave in the patient's own perspective in close third person — their fears,
their interpretations, the reasoning behind their avoidance — so that the reader
understands not just what the patient does, but why it makes sense to them. Phrases
like "she had come to believe...", "he was certain that...", "what frightened her most
was..." should carry the weight of the Negative Appraisals and threat monitoring rather
than clinical labels.

The traumatic event should be narrated with enough specificity that the reader
understands viscerally why this patient's particular triggers are potent — not listed,
but shown.

Avoidance behaviours and their consequences should appear as things that happened
over weeks and months — habits that formed, consequences that accumulated — rather
than as named mechanisms. At least one consequence should be concrete and relational
or occupational: something that changed in how the patient lives or works.

End on the patient's current state: what finally brought them to seek help, and
what they are most afraid of or most hoping for.
"""

NO_FORMULATION_SR_USER_PROMPT = """Please write a clinical vignette for the following patient.

Patient demographics:
{demographics}

Patient-reported symptoms per component:
{self_report}

Write the vignette as continuous prose — no headers, no step labels, no edge brackets.
"""

VIGNETTE_CRAFTER_NO_FORMULATION_RETRY_PROMPT = """Your previous vignette is missing some reported symptoms or demographic details. Rewrite it to include everything.

Previous vignette:
{previous_vignette}

Missing items that MUST appear in the rewrite:
{feedback}

Rewrite the full vignette (4–5 paragraphs, third person) incorporating all missing items as lived clinical experience.
Preserve all content from the previous vignette that was already correct — only add what is missing.
Do not use section headers or bullet points.
"""


# =============================================================================
# 5. VIGNETTE CRAFTER — ZERO-SHOT
# =============================================================================

ZERO_SHOT_DEMOGRAPHICS_SYSTEM_PROMPT = """You are a clinical psychologist writing psychological PTSD case vignettes.
Write in third person as a realistic personal narrative —
the kind a therapist might write after getting to know a patient over several sessions.
The vignette should describe a real person's lived experience,
not a clinical report or a list of symptoms.
Vignettes should be 500–700 words.

Important:
- Tell the story chronologically — from the traumatic event to the present
- Show symptoms through what the patient thinks, feels, and does
- Integrate the patient's occupation naturally into the story
- Do NOT end with a diagnosis or treatment recommendation
"""

ZERO_SHOT_DEMOGRAPHICS_USER_PROMPT = """Please write a clinical vignette for the following patient presenting with PTSD.

Patient demographics:
{demographics}
"""


# =============================================================================
# 6. VALIDATOR — FULL FORMULATION
# =============================================================================

VALIDATOR_VIGNETTE_SYSTEM_PROMPT = """You are a clinical validator checking whether a PTSD case
vignette accurately reflects a patient's required cognitive connections.

You will receive:
- A vignette to validate
- A list of REQUIRED edges that must appear
- A list of ACTIVE components that must appear

---

COMPONENT SYNONYMS
Each component may appear by its exact name or any accepted synonym:
  Triggers            → "triggers", "reminders", "cues", "triggering stimuli"
  Negative Appraisals → "negative appraisals", "negative beliefs", "appraisals", "distorted beliefs"
  Memory              → "intrusive memory", "trauma memory", "traumatic memory", "the memory"
  Threat              → "sense of threat", "perceived threat", "threat", "feeling of danger"
  Maladaptive Strategies → "maladaptive strategies", "avoidance", "maladaptive coping", "safety behaviours"

---

CAUSAL STANDARD
A required edge A→B is SATISFIED if, within the same paragraph:
  - Both A and B (or their synonyms) appear, AND
  - The paragraph conveys — through any language — that A influences, drives, or leads to B.
This includes direct causal sentences, sequential structure, or connecting phrases
like "because of", "this meant", "so", "which led", "as a result", "consequently", "in turn".
A required edge is MISSING only if no paragraph conveys the A→B relationship at all.

---

SECTION 1 — COMPONENT CHECK
Active components (must appear in the vignette):
{active_components}

Confirm each component appears as a described feature of the patient's presentation.
This is an internal check only — do NOT add component results to violations.

---

SECTION 2 — REQUIRED EDGES
{required_edges}

For each edge, apply the causal standard above.
- If satisfied: do nothing — only failures are reported.
- If missing: add it to violations and explain in one sentence what causal relationship is absent.
"""

VALIDATOR_VIGNETTE_USER_PROMPT = """Validate the following vignette against the cognitive graph.

{vignette}
"""


# =============================================================================
# 7. VALIDATOR — NO-FORMULATION
# =============================================================================

VALIDATOR_NO_FORMULATION_SYSTEM_PROMPT = """You are a clinical validator checking whether a PTSD case
vignette accurately reflects a patient's reported demographics and self-reported symptoms.

You will receive:
- The patient's demographics
- The patient's self-reported symptoms per PTSD component
- A vignette to validate

---

SECTION 1 — DEMOGRAPHICS CHECK
The vignette must reflect these four fields:
  - Trauma type: the described traumatic event should match the patient's reported trauma
  - Occupation: the patient's work or daily environment must appear
  - Gender: conveyed through pronouns or explicit mention
  - Age: an approximate age context must be present (exact number not required)

---

SECTION 2 — SELF-REPORT CHECK
Each reported symptom item should appear as a described experience in the vignette.
Exact wording is NOT required — clinical paraphrase or concrete illustration is sufficient.
Only flag an item if its core content is genuinely absent from the vignette.

---

JUDGMENT STANDARD
- If an item or field is reflected — even loosely, through paraphrase or concrete illustration — do NOT flag it.
- Only flag content that is genuinely absent from the vignette.
"""

VALIDATOR_NO_FORMULATION_USER_PROMPT = """Validate the following vignette.

Patient demographics:
{demographics}

Patient-reported symptoms:
{self_report}

Vignette:
{vignette}
"""


# =============================================================================
# 8. JUDGE
# =============================================================================


_JUDGE_INTRO = (
    "You are a critical reviewer of PTSD clinical vignettes for a research study.\n"
    "Rate the vignette on ONE dimension only, using the anchors below.\n"
    "Score based solely on what is written — do not infer content that is absent.\n"
    "Before scoring, identify a specific sentence that justifies your rating.\n"
)

# ── CVI ───────────────────────────────────────────────────────────────────────

JUDGE_CLARITY_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **Clarity** (1–3) — how clearly the vignette communicates this patient's experience.

1 = hard to follow. ambiguous or contradictory phrasing that never adds up to a coherent picture.
   Example: Shadows and cold hands. She remembers forgetting, the door that wasn't a door,
   Tuesday smelling wrong. Something about his voice that meant floor.

2 = readable but relies on vague or generic clinical language without specific detail.
   Example: He experienced intrusive memories that were distressing and interfered with
   his ability to function at work and maintain relationships.

3 = precise and specific — uses concrete detail that could only describe this particular
   person, not any PTSD patient.
   Example: Every time a car backfires on her street, she is already crouched behind the
   kitchen counter before she knows she has moved. She cannot sit in restaurants unless
   her back is to the wall and she can see the door — her husband has stopped suggesting otherwise.
"""

JUDGE_RELEVANCE_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **Relevance** (1–3) — clinical relevance to PTSD practice.

1 = little connection to clinical practice.
   Example: She carried the weight of what happened like a stone in her chest, always
   present, always pulling her down toward something she could not name.
2 = relevant to PTSD in general but thin — covers expected symptom domains without
   showing how or why this particular person's PTSD works the way it does.
   Example: He avoided crowded places, had nightmares several times a week, and startled
   easily at loud noises — symptoms consistent with a PTSD presentation.
3 = richly relevant — a clinician would recognise this as a case they might actually
   encounter, not a composite illustration.
   Example: She functions well enough at work that no one suspects anything, which has
   become its own trap — the energy spent on appearing intact leaves nothing for her
   evenings, and the gap between her public composure and private state has started to
   feel like evidence that she is faking it. A clinician would recognise the exhaustion
   of high-functioning concealment and the shame-driven cognitive distortion maintaining it.
"""

JUDGE_IMPORTANCE_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **Importance** (1–3) — educational value for clinical training.

1 = little value for learning.
    Example: A series of atmospheric descriptions of distress that teach
    nothing about how PTSD works or how to treat it.
2 = some learning value but teaches only generic PTSD knowledge a trainee
    could get from a textbook.
    Example: A vignette that clearly shows avoidance, hypervigilance, and
    sleep disturbance, but does not show how these connect or maintain each other.
3 = teaches something a trainee could not easily get from a textbook —
    specific clinical nuance, an unexpected presentation, or a detail that
    changes how you think about the case.
    Example: Showing how a patient's rigid eating and compulsive distraction
    feel like coping but actually increase physiological arousal, making
    triggers more potent — a maintenance cycle a trainee needs to see in action.
"""

# ── Construction quality ──────────────────────────────────────────────────────

JUDGE_G1_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **g1 — Grounded in realistic clinical experience** (1–3).

1 = generic phrasing, no specific detail, could describe any PTSD patient.
    Example: He avoided reminders of the trauma and experienced hypervigilance
    and emotional numbing that affected his relationships and work.

2 = some realistic detail but described from the outside — you can see 
    the symptoms and reactions but in terms that could fit many patients.
    Example: He lives with a constant sense of being on guard, sits with 
    his back to walls, watches people's hands. When triggered, he feels 
    panic mixed with anger. Underneath the fear there is grief for the 
    version of himself who used to feel safe.

3 = written from inside this person's specific experience — you get the 
    exact situations, the precise paradoxes, the particular reason they 
    finally sought help.
    Example: He is frightened by how real the memories still feel, but 
    also unsettled by the opposite — that something so extreme could feel 
    like it happened to somebody else. What brought him in was the fear 
    that he was no longer regaining his footing between episodes, 
    especially in the airport and during ground transport.
"""

JUDGE_G2_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **g2 — Personal narrative rather than symptom checklist** (1–3).
You can trace a specific internal logic: why this trauma led to these specific beliefs,
which drive these specific behaviours, which maintain PTSD in this specific way.

1 = no coherent through-line connecting trauma to belief to behaviour to coping.
    Example: Evocative sentences about weather, flinching, and distance from a partner,
    but no visible logic — you cannot explain why this man avoids the coastal road
    or watches his wife sleep.
2 = you can follow the person and symptoms are grounded, but the internal logic
    is partial — you see what they do but only partly why.
    Example: It is clear she checks locks and avoids her studio because she is
    frightened, but the specific beliefs driving her behaviour are not fully visible.
3 = you can trace the full line from trauma to belief to behaviour to coping —
    you understand not just what the person does but why, and how each part connects.
    Example: You can see exactly why this person's specific triggers feel threatening
    rather than just overwhelming, why their coping strategies backfire, and why
    reassurance from others cannot reach them.
"""

JUDGE_G3_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **g3 — PTSD-relevant details are explicit and identifiable** (1–3).

1 = PTSD features buried or only implied.
    Example: He found comfort in routine and kept to himself at work —
    avoidance implied but never shown as such.
2 = most features identifiable with effort.
    Example: She stopped taking commissions and her hands trembled —
    functional impairment visible, but the connection to PTSD requires
    the reader to make the link.
3 = PTSD details named and shown, not just implied.
    Example: The moment he describes waking certain the floor will give way,
    or watching his wife sleep convinced she will vanish if he stops —
    re-experiencing and hypervigilance shown in action, not just mentioned.
"""

JUDGE_G4_SYSTEM_PROMPT = _JUDGE_INTRO + """
Dimension: **g4 — Only relevant clinical information included** (1–3).

1 = contains distracting, irrelevant, or misleading content.
    Example: A paragraph about the patient's childhood, family history, or
    pre-trauma personality that has no connection to the current PTSD presentation.
2 = mostly focused with minor noise.
    Example: A sentence or two about the patient's general outlook on life
    that adds atmosphere but does not connect to any symptom or maintaining factor.
3 = every detail serves the clinical picture.
    Example: Every behavioural detail mentioned — what the patient avoids,
    how they spend their evenings, who they have stopped seeing — connects
    directly to a symptom or maintaining cycle and would leave a gap if removed.
"""

# ── DSM-5 criteria ────────────────────────────────────────────────────────────

_DSM_INTRO = (
    "Score 1 only if the criterion is clearly and explicitly present in the text — "
    "not merely inferable. Score 0 if absent or only vaguely implied.\n"
)

JUDGE_DSM_A_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion A** — traumatic event (death, serious injury, or sexual
violence — directly experienced, witnessed, or learned about) is described.

Score 1 example: A family fleeing political violence, spending months in overcrowded
transit camps with adults whose moods felt dangerous — threat of serious harm directly experienced.
Score 0 example: He had a difficult childhood and things happened that he preferred not to think about.
"""

JUDGE_DSM_B_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion B** — intrusion symptoms: flashbacks, nightmares, or
intense distress at reminders of the trauma.

Score 1 example: The memory does not return as a story but as stark silent images that
force their way in without warning, the terror so immediate it feels like the event is happening now.
Score 0 example: He sometimes thought about what had happened, especially when the weather changed.
"""

JUDGE_DSM_C_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion C** — avoidance of trauma-related thoughts/feelings,
or of external reminders (places, people, situations).

Score 1 example: He declines team events in busy restaurants, takes alternate routes
to avoid the coastal expressway, and has stopped answering automated weather alerts.
Score 0 example: He preferred quieter environments and did not like to dwell on the past.
"""

JUDGE_DSM_D_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion D** — negative alterations in cognition or mood: guilt,
shame, persistent negative beliefs, emotional numbing, detachment from others.

Score 1 example: He is certain something about him is visible to others — that anyone
who looks at him can see he comes from that history and that something is wrong with him.
Score 0 example: He felt low at times and found it hard to connect with people the way he used to.
"""

JUDGE_DSM_E_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion E** — hyperarousal or reactivity: hypervigilance,
exaggerated startle, sleep disturbance, irritability or aggression.

Score 1 example: She jolts awake multiple times a night convinced she heard a floorboard
creak, lying rigid and straining to listen, her body never fully subsiding into rest.
Score 0 example: He did not sleep well and felt on edge most of the time.
"""

JUDGE_DSM_G_SYSTEM_PROMPT = _JUDGE_INTRO + _DSM_INTRO + """
Dimension: **DSM-5 Criterion G** — clinically significant distress or functional impairment.

Score 1 example: He had to exit the elevator on the wrong floor and sit on the ground
until the shaking eased — a public breakdown that finally brought him to treatment.
Score 0 example: Things had been hard lately and he felt it was time to talk to someone.
"""

# ── Ehlers & Clark components ─────────────────────────────────────────────────

_EC_INTRO = (
    "Score 1 only if the component is explicitly shown — not just consistent with having PTSD.\n"
)

JUDGE_EC_THREAT_SYSTEM_PROMPT = _JUDGE_INTRO + _EC_INTRO + """
Dimension: **Sense of current threat** — the person feels the trauma is still happening
or still dangerous now, not merely a memory of past danger.

Score 1 example: He wakes some mornings certain the floor will give way to current —
not a memory of past danger but a present conviction that the ground itself is unsafe.
Score 0 example: He remained cautious in general and found it hard to fully relax.
"""

JUDGE_EC_APPRAISALS_SYSTEM_PROMPT = _JUDGE_INTRO + _EC_INTRO + """
Dimension: **Negative appraisals** — catastrophic or overly negative interpretation
of the trauma or its aftermath (e.g. "I am permanently damaged", "It was my fault").

Score 1 example: When he notices himself scanning exits or recoiling from an ordinary
approach, it confirms his private conviction that something is defective about him and
that he cannot inhabit the world normally.
Score 0 example: He felt bad about how he had been acting and worried he was not coping well.
"""

JUDGE_EC_MEMORY_SYSTEM_PROMPT = _JUDGE_INTRO + _EC_INTRO + """
Dimension: **Nature of trauma memory** — fragmented, disorganised, feels like happening
now rather than in the past (as opposed to an ordinary autobiographical memory).

Score 1 example: The memory does not come back as a story — it arrives as a series of
stark disconnected images (the glint of broken glass, the reflection of a shape in a mirror)
that feel present rather than past.
Score 0 example: He had vivid memories of what happened that came back to him at difficult moments.
"""

JUDGE_EC_STRATEGIES_SYSTEM_PROMPT = _JUDGE_INTRO + _EC_INTRO + """
Dimension: **Maladaptive coping strategies** — behaviours that maintain PTSD:
avoidance, thought suppression, rumination, substance use, safety behaviours.
The key is that the strategy is shown to backfire or perpetuate symptoms.

Score 1 example: He restricts his eating rigidly not for weight reasons but because it
is the one domain where he can impose control — a strategy that depletes him physically
and makes triggers more potent.
Score 0 example: He tried to keep busy and avoid thinking about things that upset him.
"""

JUDGE_EC_TRIGGERS_SYSTEM_PROMPT = _JUDGE_INTRO + _EC_INTRO + """
Dimension: **Triggers for re-experiencing** — specific internal or external cues that
reliably activate trauma memory or distress.

Score 1 example: The smell of alcohol makes his chest seize before he has located its
source — a sensory cue not obviously linked to the original trauma that reliably sets off alarm.
Score 0 example: Certain situations reminded him of what happened and caused him distress.
"""

# ── Shared user prompt ────────────────────────────────────────────────────────

JUDGE_USER_PROMPT = """Rate the following clinical vignette:

{vignette}
"""
