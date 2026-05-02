PIPELINES: dict[str, list[str]] = {
    "craft_persona":         ["craft_persona"],
    "vignette":              ["persona", "validate_vignette"],
    "vignette_no_val":       ["persona"],
    "vignette_full":         ["craft_persona", "persona", "validate_vignette"],
    "vignette_from_persona": ["load_persona", "persona", "validate_vignette"],
    "zero_shot":             ["zero_shot"],
}
