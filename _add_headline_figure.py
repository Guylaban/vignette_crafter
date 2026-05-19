import nbformat

NB_PATH = "analysis/vignette_embedding_analysis.ipynb"
NEW_ID = "headline_trauma_grouping_tsne"
AFTER_ID = "per_model_umap_static_grid"

SOURCE = r'''# Cell: Headline figure - 4 representative models, 6 trauma groups, silhouette
# annotations. Built on cached t-SNE coords from section 4.

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score

# 1. Trauma type -> broad group mapping (6 groups)
TRAUMA_GROUPS = {
    # Interpersonal violence
    "Assault":                            "Interpersonal violence",
    "Mugging or robbery":                 "Interpersonal violence",
    "Physical abuse by romantic partner": "Interpersonal violence",
    "Rape":                               "Interpersonal violence",
    "Sexual assault":                     "Interpersonal violence",
    "Stalking":                           "Interpersonal violence",
    "Police":                             "Interpersonal violence",
    "Police violence":                    "Interpersonal violence",
    # War and conflict
    "Combat":                  "War and conflict",
    "Military":                "War and conflict",
    "Civilian in war zone":    "War and conflict",
    "Refugee":                 "War and conflict",
    "Relief worker in war zone": "War and conflict",
    "Terrorism":               "War and conflict",
    "Captivity":               "War and conflict",
    "Torture":                 "War and conflict",
    # Accidents and disasters
    "Natural disaster":                                "Accidents and disasters",
    "Man-made disaster":                               "Accidents and disasters",
    "Life-threatening accident":                       "Accidents and disasters",
    "Life-threatening motor vehicle collision":        "Accidents and disasters",
    "Toxic chemical exposure":                         "Accidents and disasters",
    "Accidentally caused serious injury to another":   "Accidents and disasters",
    # Health crises
    "Life-threatening illness":         "Health crises",
    "Child's life-threatening illness": "Health crises",
    # Childhood abuse
    "Physical abuse by caregiver (childhood)": "Childhood abuse",
    "Witnessed domestic violence (childhood)": "Childhood abuse",
    # Loss and witnessing
    "Trauma to a loved one":                       "Loss and witnessing",
    "Unexpected or traumatic death of a loved one":"Loss and witnessing",
    "Witnessed other trauma":                      "Loss and witnessing",
}
GROUP_ORDER = [
    "Interpersonal violence",
    "War and conflict",
    "Childhood abuse",
    "Accidents and disasters",
    "Health crises",
    "Loss and witnessing",
]
# Distinct, high-contrast colors (Plotly D3 + extras), one per group
GROUP_COLORS = {
    "Interpersonal violence":  "#EF553B",  # red
    "War and conflict":        "#636EFA",  # blue
    "Childhood abuse":         "#AB63FA",  # purple
    "Accidents and disasters": "#FFA15A",  # orange
    "Health crises":           "#00CC96",  # green
    "Loss and witnessing":     "#19D3F3",  # cyan
}

# 2. Attach trauma group to df
if "_trauma_type" not in df.columns:
    _demo = (pd.read_csv(ANALYSIS_DIR / "personas_long.csv")
               [["persona_id", "trauma_type"]]
               .drop_duplicates("persona_id")
               .set_index("persona_id"))
    df["_trauma_type"] = df["persona_id"].map(_demo["trauma_type"])
df["_trauma_group"] = df["_trauma_type"].map(TRAUMA_GROUPS)

unmapped = df.loc[df["_trauma_type"].notna() & df["_trauma_group"].isna(),
                  "_trauma_type"].unique()
if len(unmapped):
    print(f"WARN: {len(unmapped)} trauma types unmapped: {list(unmapped)}")

CONDITION_LABELS_LOCAL = {
    "full":           "Full formulation",
    "no_formulation": "No formulation",
    "zero_shot":      "Zero-shot",
}

# 3. Silhouette per (model, condition) using 2D t-SNE coords + trauma group label
sil_rows = []
for model in sorted(df["model"].unique()):
    row = {"model": model}
    for cond in CONDITION_LABELS_LOCAL:
        cond_mask = (df["condition"] == cond).values
        coords = tsne_coords[cond]
        sub_df = df.loc[cond_mask].reset_index(drop=True)
        m_mask = (sub_df["model"] == model).values
        sub_coords = coords[m_mask]
        sub_groups = sub_df.loc[m_mask, "_trauma_group"].values
        valid = pd.notna(sub_groups)
        sub_coords = sub_coords[valid]
        sub_groups = sub_groups[valid]
        if len(sub_coords) < 5 or len(set(sub_groups)) < 2:
            row[cond] = np.nan
            continue
        try:
            row[cond] = float(silhouette_score(sub_coords, sub_groups))
        except Exception:
            row[cond] = np.nan
    sil_rows.append(row)

sil_df = pd.DataFrame(sil_rows).set_index("model")
print("Silhouette by trauma group on 2D t-SNE coords (higher = more clustered):")
print(sil_df.round(3).to_string())
print()

# 4. Pick 4 representative models by zero-shot silhouette range
#    Override by setting MODELS_TO_SHOW = ["...", "...", "...", "..."]
MODELS_TO_SHOW = None

if MODELS_TO_SHOW is None:
    ranked = sil_df["zero_shot"].dropna().sort_values(ascending=False)
    n = len(ranked)
    pick_idx = sorted({0, max(1, n // 3), max(2, 2 * n // 3), n - 1})
    MODELS_TO_SHOW = [ranked.index[i] for i in pick_idx]
    print(f"Auto-picked 4 models spanning zero-shot silhouette range:")
    for m in MODELS_TO_SHOW:
        print(f"  {m}  (zero-shot silhouette = {ranked[m]:.3f})")
    print()

# 5. Build figure
n_rows = len(MODELS_TO_SHOW)
n_cols = len(CONDITION_LABELS_LOCAL)
fig, axes = plt.subplots(n_rows, n_cols,
                         figsize=(11.5, 2.9 * n_rows),
                         squeeze=False)

for i, model in enumerate(MODELS_TO_SHOW):
    for j, cond in enumerate(CONDITION_LABELS_LOCAL):
        ax = axes[i, j]
        cond_mask = (df["condition"] == cond).values
        coords = tsne_coords[cond]
        sub_df = df.loc[cond_mask].reset_index(drop=True)
        m_mask = (sub_df["model"] == model).values
        sub_model = sub_df.loc[m_mask].reset_index(drop=True)
        model_coords = coords[m_mask]
        for g in GROUP_ORDER:
            g_mask = (sub_model["_trauma_group"] == g).values
            if not g_mask.any():
                continue
            ax.scatter(
                model_coords[g_mask, 0], model_coords[g_mask, 1],
                c=GROUP_COLORS[g], s=14, alpha=0.82,
                edgecolors="none", label=g,
            )
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_alpha(0.3); spine.set_linewidth(0.6)
        if i == 0:
            ax.set_title(CONDITION_LABELS_LOCAL[cond],
                         fontsize=11, fontweight="bold")
        if j == 0:
            ax.set_ylabel(model, fontsize=10,
                          rotation=0, ha="right", va="center", labelpad=10)
        s = sil_df.loc[model, cond]
        if pd.notna(s):
            ax.text(0.97, 0.04, f"sil = {s:.2f}",
                    transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=8, color="black",
                    bbox=dict(facecolor="white", alpha=0.85,
                              edgecolor="none", pad=2))

handles = [plt.Line2D([0], [0], marker="o", linestyle="",
                       markersize=8, markerfacecolor=GROUP_COLORS[g],
                       markeredgecolor="none", label=g) for g in GROUP_ORDER]
fig.legend(handles=handles, labels=GROUP_ORDER,
           loc="lower center", bbox_to_anchor=(0.5, -0.01),
           ncol=3, fontsize=9, frameon=False,
           title="Trauma category", title_fontsize=10,
           columnspacing=1.5, handletextpad=0.4)

fig.suptitle(
    "Persona formulations dampen trauma-type stereotyping in LLM vignettes",
    fontsize=12, y=1.001, fontweight="bold",
)
fig.tight_layout(rect=(0.0, 0.05, 1.0, 1.0))

OUT_PNG = ANALYSIS_DIR / "headline_trauma_grouping_tsne.png"
OUT_PDF = ANALYSIS_DIR / "headline_trauma_grouping_tsne.pdf"
OUT_CSV = ANALYSIS_DIR / "silhouette_by_trauma_group.csv"
fig.savefig(OUT_PNG, dpi=170, bbox_inches="tight", facecolor="white")
fig.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
sil_df.round(4).to_csv(OUT_CSV)
plt.show()
print(f"Saved -> {OUT_PNG.name}")
print(f"Saved -> {OUT_PDF.name}")
print(f"Saved -> {OUT_CSV.name}")
'''

nb = nbformat.read(NB_PATH, as_version=4)
ids = [c.get("id") for c in nb.cells]
if NEW_ID in ids:
    idx = ids.index(NEW_ID)
    nb.cells[idx].source = SOURCE
    nb.cells[idx].outputs = []
    nb.cells[idx].execution_count = None
    print(f"Replaced {NEW_ID} at position {idx}.")
else:
    idx = ids.index(AFTER_ID)
    new_cell = nbformat.v4.new_code_cell(source=SOURCE)
    new_cell["id"] = NEW_ID
    nb.cells.insert(idx + 1, new_cell)
    print(f"Inserted {NEW_ID} after {AFTER_ID} at position {idx + 1}.")
nbformat.write(nb, NB_PATH)
