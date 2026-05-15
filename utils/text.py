"""Text utilities for cleaning vignette output."""

import re


def normalize_punctuation(text: str) -> str:
    """Replace smart/fancy Unicode punctuation with plain ASCII equivalents."""
    if not text:
        return text
    text = text.replace("‘", "'").replace("’", "'")  # ' '
    text = text.replace("“", '"').replace("”", '"')  # " "
    text = text.replace("–", "-").replace("—", "-")  # – —
    text = text.replace("‑", "-")                          # non-breaking hyphen
    text = text.replace("→", "->")                         # arrow
    text = text.replace("…", "...")                        # …
    return text


def strip_markdown(text: str) -> str:
    """Remove markdown symbols from vignette text, preserving prose content.

    Handles: headings (#), bold (**text** / __text__), italic (*text* / _text_),
    horizontal rules (---), and leading list markers (- / * at line start).
    """
    if not text:
        return text

    # Remove headings (# Title → Title)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)

    # Remove italic: *text* or _text_  (single, not double)
    text = re.sub(r"\*(.+?)\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_(.+?)_", r"\1", text, flags=re.DOTALL)

    # Remove horizontal rules
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove leading list markers (- item or * item at line start)
    text = re.sub(r"^[-*]\s+", "", text, flags=re.MULTILINE)

    # Normalise smart/fancy punctuation to plain ASCII
    text = normalize_punctuation(text)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
