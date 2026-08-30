# Task Instructions

## Background

You are evaluating synthetic PTSD case vignettes for causal connections between
five cognitive components drawn from the Ehlers & Clark (2000) cognitive model
of PTSD:

1. **Triggers** — reminders and cues that re-activate the trauma memory.
2. **Negative Appraisals** — beliefs about self / world / trauma / future
   (e.g. *"I am permanently damaged"*, *"the world is dangerous"*).
3. **Memory** — the intrusive trauma memory itself (flashbacks, sensory
   reliving, fragmented recall).
4. **Threat** — the sense of ongoing, current danger (hypervigilance, being on
   edge, feeling the trauma is about to happen again).
5. **Maladaptive Strategies** — avoidance, safety behaviours, thought
   suppression, substance use, hypervigilant checking.

This is the same task an automated judge performed in our study. Your ratings
are the human reference standard against which that judge is validated, so
please follow the rubric exactly and rate every edge of every vignette.

## The two ratings

For each of the 20 ordered pairs A → B (A ≠ B) in each vignette:

### 1. Present (0 or 1) — strict binary standard

Edge A → B is PRESENT (1) **iff**, within the same paragraph:

1. **Both A and B appear** (by label, synonym, or clear phenomenological
   description); AND
2. **The paragraph conveys that A influences / drives / leads to B**, via
   direct causal language (*because*, *triggered*, *led to*, *as a result*,
   *which meant*, *in turn*), sequential structure (A then B as its
   unmistakable consequence), or structural connectives (*"every time X, Y"*).

Otherwise 0. **Mere co-occurrence is not enough. Direction matters** — rate
A → B and B → A independently.

### 2. Strength (raw continuous score, 0.0 to 1.0)

This is a **raw, free continuous estimate** of how strongly the text conveys
A driving B. **Use the whole range and any value you like** (two decimals are
fine). Only the endpoints are fixed:

- **0.0** = no causal link from A to B in the text at all
- **1.0** = the strongest, most explicit and emphatic causal link possible

Everything in between is a smooth continuum: the clearer, more direct, and more
emphatic the causal connection, the higher the number. **Do not snap to preset
levels** — give your honest continuous judgement. `strength` may be above 0
even when `present = 0` if there is any trace of the link; set `strength = 0.0`
only when there is no trace at all. See `RUBRIC.md` for calibration examples.

## Component synonyms

| Component | Synonyms |
|-----------|----------|
| Triggers | triggers, reminders, cues, triggering stimuli, sensory cues |
| Negative Appraisals | negative appraisals, negative beliefs, appraisals, distorted beliefs, catastrophic thoughts |
| Memory | intrusive memory, trauma memory, traumatic memory, the memory, flashbacks, sensory reliving |
| Threat | sense of threat, perceived threat, threat, feeling of danger, hypervigilance, feeling unsafe |
| Maladaptive Strategies | maladaptive strategies, avoidance, safety behaviours, coping, checking, substance use, thought suppression |

A clear description of the phenomenon counts even without the label word.

## The rating form

`rating_form.csv` has **one row per vignette** (150 rows). Each row contains:

- `vignette_id` — V001 … V150
- `vignette` — the full vignette text (also provided as `vignettes/Vxx.txt`
  if you prefer reading in a text editor)
- 20 columns `present__<A>__to__<B>` — fill each with 0 or 1
- 20 columns `strength__<A>__to__<B>` — fill each with 0.0–1.0
- `notes` — free text for borderline calls

Column names use underscores for spaces, e.g.
`present__Triggers__to__Negative_Appraisals` is the edge
Triggers → Negative Appraisals.

**Workflow per vignette:** read the vignette fully once; walk the 20 present
columns left to right; then the 20 strength columns (or fill both together,
edge by edge); note anything borderline. Every one of the 40 rating cells in
every row must be filled — no blanks.

## What you should NOT do

- Do not try to guess how each vignette was generated (they are shuffled and
  unlabelled deliberately).
- Do not rate clinical quality, plausibility, or diagnostic accuracy — only
  the edges.
- Do not leave any rating cell empty.
- Do not consult anyone else or any tool about a specific vignette; this is a
  single-rater reliability measurement.

## Pacing

Aim for **4–6 minutes per vignette** (**10–15 hours total** — this is a
multi-day task). Do at most **15 vignettes per sitting**, with a break of at
least an hour between sittings — rater fatigue degrades reliability. Plan
~10–12 sittings, or split the work across raters by vignette blocks.

## Delivery

Save the completed `rating_form.csv` (keep it as .csv) and send it back to the
coordinator. Partial forms are still useful if you must stop early.
