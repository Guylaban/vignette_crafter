"""Ehlers & Clark PTSD formulation — directed causal graph."""

COMPONENT_SYNONYMS: dict[str, list[str]] = {
    "Triggers":               ["triggering stimuli", "triggers", "reminders", "cues"],
    "Negative Appraisals":    ["negative appraisals", "negative beliefs", "distorted beliefs", "appraisals"],
    "Memory":                 ["intrusive memory", "traumatic memory", "trauma memory", "the memory"],
    "Threat":                 ["sense of threat", "perceived threat", "feeling of danger", "threat"],
    "Maladaptive Strategies": ["maladaptive strategies", "safety behaviours", "maladaptive coping", "avoidance"],
}

DIRECT_EDGES: dict = {
    ("Triggers", "Maladaptive Strategies"): 0,
    ("Triggers", "Threat"): 0,
    ("Triggers", "Memory"): 0,
    ("Triggers", "Negative Appraisals"): 0,
    ("Negative Appraisals", "Maladaptive Strategies"): 0,
    ("Negative Appraisals", "Threat"): 0,
    ("Negative Appraisals", "Memory"): 0,
    ("Negative Appraisals", "Triggers"): 0,
    ("Memory", "Maladaptive Strategies"): 0,
    ("Memory", "Threat"): 0,
    ("Memory", "Negative Appraisals"): 0,
    ("Memory", "Triggers"): 0,
    ("Threat", "Maladaptive Strategies"): 0,
    ("Threat", "Memory"): 0,
    ("Threat", "Negative Appraisals"): 0,
    ("Threat", "Triggers"): 0,
    ("Maladaptive Strategies", "Memory"): 0,
    ("Maladaptive Strategies", "Negative Appraisals"): 0,
    ("Maladaptive Strategies", "Triggers"): 0,
    ("Maladaptive Strategies", "Threat"): 0,
}

EDGE_EXAMPLES: dict[tuple[str, str], list[str]] = {
    ("Triggers", "Memory"): [
        "The smell of his cologne in the lift sent the whole night flooding back before she had even reached her floor.",
        "Hearing that song on the radio dragged her straight back into the room where it happened, as if no time had passed at all.",
        "Walking past the bus stop where it occurred, she was no longer on the street — she was back there, every detail sharp and close.",
    ],
    ("Triggers", "Negative Appraisals"): [
        "Every time she walked through that car park, the thought arrived with her: this is what your life is now — flinching at nothing.",
        "Seeing a man in the same jacket made her think, with quiet certainty, that she would never stop being afraid.",
        "The sound of raised voices next door told her, with a logic she couldn't argue with, that nowhere was ever really safe.",
    ],
    ("Triggers", "Threat"): [
        "The cues led to a feeling of danger that felt as real as the original event.",
        "A knock at the door after dark sent her heart into her throat — her body read it as an emergency, even when her mind knew better.",
        "Sitting in the waiting room, she noticed a man watching her from across the room and felt the same cold certainty: something terrible was about to happen.",
    ],
    ("Triggers", "Maladaptive Strategies"): [
        "She stopped taking that route to work entirely — better to add twenty minutes to her commute than to feel that way again.",
        "When the anniversary came around, she kept herself moving all day, cleaning, cooking, anything, because sitting still meant the thoughts would catch up.",
        "She started leaving events early, telling herself she was tired, because staying too long meant the chances of something going wrong only multiplied.",
    ],
    ("Memory", "Triggers"): [
        "After the memory had surfaced, even the most ordinary things — a kettle whistling, a door slamming — felt like warnings she couldn't afford to ignore.",
        "The intrusive image left her scanning every room she entered, cataloguing exits, tracking faces, unable to switch off.",
        "Because the memory came back so vividly, she began to see threads of it everywhere: in strangers' faces, in certain times of day, in the quality of winter light.",
    ],
    ("Memory", "Negative Appraisals"): [
        "After the image broke through again, she caught herself thinking: if this keeps happening, there must be something deeply wrong with me.",
        "The memory surfaced in the middle of a meeting and she spent the rest of the day convinced that everyone around her could see how broken she was.",
        "Each time the flashback came, the thought that followed it was always the same — that she had let this happen, and that it said something permanent about who she was.",
    ],
    ("Memory", "Threat"): [
        "Once the memory had surfaced, she couldn't shake the sense that the danger was still present — that it had simply moved into her body rather than gone away.",
        "The flashback left her standing in her own kitchen feeling hunted, even with the door locked and the lights on.",
        "After the memory broke through, the threat felt immediate and physical — not something that had happened, but something that was still happening.",
    ],
    ("Memory", "Maladaptive Strategies"): [
        "She had learned that if she kept the television on loud enough, the thoughts couldn't get a foothold — silence was the enemy.",
        "After the memory surfaced during sex, she began finding quiet reasons to avoid intimacy altogether, telling herself she was simply tired or stressed.",
        "To stop the images coming at night, she started staying up later and later, until exhaustion was the only reliable way to fall asleep.",
    ],
    ("Negative Appraisals", "Memory"): [
        "The belief that she was permanently changed kept bringing her back to the moment it had happened, as if she needed to locate exactly where she had been lost.",
        "Telling herself that she should have seen it coming made the memory more vivid and easier to find — it sat there waiting, proof of her failure.",
        "The conviction that she was weak fed directly into the flashback, colouring it, making it worse: she wasn't just there again, she was there again and helpless.",
    ],
    ("Negative Appraisals", "Triggers"): [
        "Once she had concluded that the world was fundamentally unsafe, almost anything could confirm it — a figure in her periphery, the wrong tone of voice, footsteps behind her.",
        "The belief that she couldn't trust her own judgement meant that things she would once have registered and dismissed now snagged and held her attention.",
        "Her conviction that it would happen again meant she moved through ordinary days as if they were mined — every ambiguity became a potential signal.",
    ],
    ("Negative Appraisals", "Threat"): [
        "Having decided that she was permanently vulnerable, she walked into rooms already braced — the threat arrived with her before anything had happened.",
        "The belief that she was a target — not unlucky, but chosen — meant that every unfamiliar face carried a weight of potential danger.",
        "Her certainty that she couldn't protect herself made every new situation feel like a test she was already failing.",
    ],
    ("Negative Appraisals", "Maladaptive Strategies"): [
        "If she had concluded that the world was dangerous and she was defenceless, staying home wasn't avoidance — it was the only rational thing to do.",
        "The belief that speaking about it would make things worse kept her silent in her sessions, offering fragments instead of the whole picture.",
        "Having decided that her feelings couldn't be trusted, she worked hard to stay numb — and had become quite good at it.",
    ],
    ("Threat", "Memory"): [
        "Walking home on high alert, she passed a doorway and the memory was simply there — pulled out of her by the adrenaline, fully formed.",
        "The persistent sense of danger kept her close to the event in her mind, as if she needed to keep reviewing it to stay one step ahead of whatever came next.",
        "On nights when the threat felt highest, the memory was hardest to keep at bay — it would surface in the dark, vivid and unwelcome.",
    ],
    ("Threat", "Triggers"): [
        "Already running on threat, she found that almost anything could tip into a warning — a van parked at an odd angle, a light left on that shouldn't have been.",
        "The background hum of danger she carried everywhere made ordinary cues feel like messages — each one confirming what her body already believed.",
        "Living at that pitch of alertness, she found the world had become dense with reminders she couldn't stop reading.",
    ],
    ("Threat", "Negative Appraisals"): [
        "The constant sense of danger was the most convincing proof she had that her life had changed beyond repair.",
        "Feeling this afraid all the time, she had eventually come to accept the conclusion her body kept offering: that she was not the kind of person who got to feel safe.",
        "The threat that shadowed her days quietly confirmed the thought she worked hardest to resist — that this was simply who she was now.",
    ],
    ("Threat", "Maladaptive Strategies"): [
        "When the threat felt this close, planning her exit from every room she entered wasn't a symptom — it was just sensible.",
        "She had found that checking the locks twice was the only thing that allowed her body to settle enough to sleep, so she checked them twice.",
        "The only way to move through the world at that level of fear was to make it smaller — fewer places, fewer people, fewer chances for something to go wrong.",
    ],
    ("Maladaptive Strategies", "Memory"): [
        "She had been avoiding any mention of it for so long that when the memory finally surfaced, it was louder than it had ever been — all that suppression had kept it fresh.",
        "Not talking about it meant the memory had never been put anywhere; it remained in her, undisturbed and intact, exactly where she had left it.",
        "The effort of keeping it at a distance had paradoxically kept it close — she had thought about not thinking about it every day for three years.",
    ],
    ("Maladaptive Strategies", "Triggers"): [
        "Each place she avoided became a reminder in itself — the long way round she walked every morning was its own daily acknowledgement of what had happened.",
        "Her safety behaviours had drawn a map of the event around her: everything she couldn't do, everywhere she couldn't go, every person she kept at arm's length.",
        "The avoidance had grown in all directions until the city was full of routes she no longer used and things she could no longer say.",
    ],
    ("Maladaptive Strategies", "Negative Appraisals"): [
        "Three years of avoiding it had told her something she couldn't easily argue with: that she must be more fragile than other people, or she would have been over this by now.",
        "Each time she used a safety behaviour to get through the day, she felt the quiet accumulation of evidence that she couldn't cope without it.",
        "The fact that she still needed to do all of this — the checking, the planning, the long way round — confirmed, in some wordless way, that she wasn't getting better.",
    ],
    ("Maladaptive Strategies", "Threat"): [
        "Never having stayed in a situation long enough to find out it was safe, her body had never received the evidence it needed — the threat remained as high as the day it was set.",
        "The checking and the avoidance had kept her alive, in her nervous system's accounting, which meant the danger they were responding to must be real and ongoing.",
        "Without ever testing the feeling, she had no way to know that the threat was not what her body insisted it was — the safety behaviours had sealed that possibility off.",
    ],
}
