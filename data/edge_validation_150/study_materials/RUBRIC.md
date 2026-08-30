# Rating Rubric

You give **two ratings per directed edge**, 20 edges per vignette.

> **Present (0/1):** edge A → B is 1 iff some paragraph names both A and B (or
> synonyms / clear description) and conveys that A drives / leads to B.
> Otherwise 0. Mere co-occurrence is not enough; direction matters.
>
> **Strength (raw 0.0–1.0):** a free continuous estimate of how strongly the
> text conveys A driving B. 0.0 = no link at all; 1.0 = strongest, most
> explicit causal link possible. Use any value in between — do not snap to
> preset levels.

The strength score is **not** a set of buckets. Treat it like a dial: read the
passage, ask "how strong and explicit is this causal connection?", and place it
anywhere on 0–1. The examples below are calibration points, not the only
allowed values.

---

## Calibration examples (present = 1 unless noted)

| Passage (edge) | Present | Strength (a reasonable value) |
|----------------|---------|-------------------------------|
| *"The smell of antiseptic **triggered** the memory of the accident."* (Triggers → Memory) | 1 | **0.90** — direct causal verb, unambiguous |
| *"Because crowded trains set him off, he now walks two hours to work instead."* (Triggers → Maladaptive Strategies) | 1 | **0.95** — explicit *because*, strong |
| *"She could not stop thinking the world was unsafe, and she avoided leaving the house as a result."* (Negative Appraisals → Maladaptive Strategies) | 1 | **0.85** — clear connective *as a result* |
| *"Every time she felt on edge, she would check the locks."* (Threat → Maladaptive Strategies) | 1 | **0.55** — clear direction, but structural not stated |
| *"He saw a man in a hoodie. His heart hammered; he was sure he was about to be attacked."* (Triggers → Threat) | 1 | **0.45** — sequential, no causal word |
| *"The image would flood back, and each time she felt the ceiling was about to give way."* (Memory → Threat) | 1 | **0.50** — implied by *each time*, phenomenological |
| *"The nightmares left her exhausted. Most evenings she drank until she could sleep without dreaming."* (Memory → Maladaptive Strategies) | borderline | **0.30** — inferable but not carried explicitly; a note helps |
| *"She had intrusive memories and often felt on edge during the day."* (Memory → Threat) | 0 | **0.12** — co-occurrence only, faint trace, fails the strict present bar |
| *P1 mentions memories; P3 mentions checking locks (no shared paragraph).* (Memory → Maladaptive Strategies) | 0 | **0.00** — no trace of the directed link |
| *"The compulsive checking left her more certain the world was dangerous."* (reverse: Negative Appraisals → Maladaptive Strategies) | 0 | **0.00** — the text carries the other direction, not this one |

Notice the strength values are spread continuously (0.00, 0.12, 0.30, 0.45,
0.50, 0.55, 0.85, 0.90, 0.95) — pick whatever number matches the passage, not
the nearest label.

---

## How the two ratings relate

- **Present** is the strict yes/no: does a paragraph actually carry the
  directed causal link? (Same standard the automated judge used.)
- **Strength** is your raw feel for how strong that link is, on a full 0–1
  dial. It can be non-zero on a present = 0 edge if there's a faint trace
  (that's how we learn where your yes/no cutoff sits on the dial).
- If the edge is completely absent (no trace at all): present = 0, strength = 0.00.

---

## One example phrasing per edge (calibration for what each edge looks like)

Each would rate present = 1; the strength shown reflects that phrasing.

| Edge | Example phrasing (a reasonable strength) |
|------|------------------------------------------|
| Triggers → Negative Appraisals | *"Each knock at the door confirmed her belief she'd never be safe."* (0.75) |
| Triggers → Memory | *"The diesel smell threw him back into the crash."* (0.90) |
| Triggers → Threat | *"When the fireworks started she was instantly sure something terrible was coming."* (0.60) |
| Triggers → Maladaptive Strategies | *"Because crowds set him off, he now avoids the town centre entirely."* (0.90) |
| Negative Appraisals → Triggers | *"Certain danger was everywhere, she began seeing reminders in ordinary objects."* (0.50) |
| Negative Appraisals → Memory | *"Dwelling on how he failed them always dragged the images back."* (0.80) |
| Negative Appraisals → Threat | *"Believing the world had shown its true face, she felt unsafe even at home."* (0.70) |
| Negative Appraisals → Maladaptive Strategies | *"Sure others saw her as broken, she stopped answering their calls."* (0.90) |
| Memory → Triggers | *"As the flashbacks worsened, everyday sounds began to act as reminders."* (0.50) |
| Memory → Negative Appraisals | *"Every intrusion deepened his conviction he was permanently damaged."* (0.80) |
| Memory → Threat | *"When the memory surfaced, the danger felt current, as if happening now."* (0.80) |
| Memory → Maladaptive Strategies | *"To keep the images away, she drank until she fell asleep."* (0.90) |
| Threat → Triggers | *"Constantly on alert, he picked up on cues that had never registered before."* (0.50) |
| Threat → Negative Appraisals | *"The relentless sense of danger convinced her something in her had broken."* (0.70) |
| Threat → Memory | *"Whenever the danger spiked, fragments of that afternoon forced their way back."* (0.60) |
| Threat → Maladaptive Strategies | *"Feeling under threat, he slept with the lights on and checked the locks hourly."* (0.80) |
| Maladaptive Strategies → Triggers | *"The more she avoided the area, the more its name on a sign became a reminder."* (0.50) |
| Maladaptive Strategies → Negative Appraisals | *"Each time he numbed himself with drink, he woke more sure he was beyond repair."* (0.70) |
| Maladaptive Strategies → Memory | *"Suppressing the thoughts all day meant they returned at night, more vivid."* (0.70) |
| Maladaptive Strategies → Threat | *"Avoiding every reminder kept the sense that danger was everywhere fully alive."* (0.60) |

---

## Boundary rules

1. **Direction matters.** *"The memory makes her feel unsafe"* is Memory →
   Threat; the reverse (Threat → Memory) is 0 / 0.00 unless the text separately
   conveys it. Rate each direction independently.
2. **Causal chain of three.** *"The reminder set off the memory, which in turn
   convinced her the danger was current."* → Triggers → Memory and Memory →
   Threat each get a real value; the transitive Triggers → Threat stays 0 /
   0.00 unless a paragraph separately carries it.
3. **Repeated edge across paragraphs.** One edge, one pair of cells — rate the
   strongest instance.
4. **Components in different paragraphs, never joined.** present = 0,
   strength = 0.00.
5. **Faint trace / co-occurrence.** present = 0, strength small but non-zero
   (e.g. 0.05–0.2), and add a note.

## Per-edge checklist

1. Any paragraph with both A and B? — No → present 0; strength 0.00 (or a small
   value if there's a faint cross-sentence trace).
2. Does that paragraph convey A driving B? — decides present (1 = yes).
3. Right direction (A → B, not B → A)? — No → present 0 for this direction.
4. **Strength:** independent of the 0/1, set the dial by how strong and
   explicit the causal link reads — anywhere 0.00–1.00.
5. Repeat for the reverse edge B → A.
