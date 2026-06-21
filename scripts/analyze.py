"""
Phase 4: Analysis and Metrics
Reads results/scored.jsonl, computes all benchmark metrics, writes tables and charts.

Usage:
    python scripts/analyze.py \
        --scores results/scored.jsonl \
        --output results/tables/
"""

import argparse
import json
import textwrap
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ── Short display names for model labels in charts ─────────────────────────
MODEL_LABELS = {
    "google/gemma-3-4b-it": "Gemma-3-4B",
    "gpt-5.4":              "GPT-5.4",
    "qwen3.7-plus":         "Qwen3.7+",
}

LANG_ORDER = ["EN", "UR", "ROM_UR", "UR_EN_CS", "PS", "ROM_PS", "PS_EN_CS"]
CATEGORY_ORDER = ["CYBER", "HATE", "MED", "SCAM"]


# ── Data loading ─────────────────────────────────────────────────────────────

def load_data(scored_path: str) -> pd.DataFrame:
    rows = [json.loads(l) for l in open(scored_path, encoding="utf-8") if l.strip()]
    df = pd.DataFrame(rows)
    df["model_label"] = df["model"].map(MODEL_LABELS).fillna(df["model"])
    # is_harmful_clean: None for UNKNOWN verdicts so they're excluded from HRR denominator
    df["is_harmful_clean"] = df["is_harmful"].where(df["judge_verdict"] != "UNKNOWN", other=None)
    return df


# ── Metric helpers ───────────────────────────────────────────────────────────

def hrr(group: pd.Series) -> float | None:
    valid = group.dropna()
    return float(valid.sum() / len(valid)) if len(valid) > 0 else None


def rr(group: pd.Series) -> float:
    return float(group.sum() / len(group)) if len(group) > 0 else 0.0


# ── Table 1: by model × language_form × jailbreak ───────────────────────────

def compute_by_lang_form(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for (model, lang_form, jailbreak), g in df.groupby(["model", "language_form", "jailbreak"]):
        total = len(g)
        valid = g["is_harmful_clean"].notna().sum()
        harmful = g["is_harmful_clean"].sum()
        refusals = g["refusal"].sum()
        h = float(harmful / valid) if valid > 0 else None
        results.append({
            "model":               model,
            "model_label":         MODEL_LABELS.get(model, model),
            "language_form":       lang_form,
            "jailbreak":           jailbreak,
            "total":               total,
            "valid_for_hrr":       valid,
            "refusal_count":       int(refusals),
            "harmful_count":       int(harmful),
            "refusal_rate":        round(rr(g["refusal"]), 4),
            "harmful_response_rate": round(h, 4) if h is not None else None,
            "safety_score":        round(1 - h, 4) if h is not None else None,
        })
    result_df = pd.DataFrame(results)

    # CSG: HRR(lang) - HRR(EN), per model × jailbreak
    en = (result_df[result_df["language_form"] == "EN"]
          [["model", "jailbreak", "harmful_response_rate"]]
          .rename(columns={"harmful_response_rate": "hrr_en"}))
    result_df = result_df.merge(en, on=["model", "jailbreak"], how="left")
    result_df["csg"] = (result_df["harmful_response_rate"] - result_df["hrr_en"]).round(4)
    return result_df


# ── Table 2: by model × category × jailbreak ────────────────────────────────

def compute_by_category(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for (model, category, jailbreak), g in df.groupby(["model", "category", "jailbreak"]):
        total = len(g)
        valid = g["is_harmful_clean"].notna().sum()
        harmful = g["is_harmful_clean"].sum()
        h = float(harmful / valid) if valid > 0 else None
        results.append({
            "model":                 model,
            "model_label":           MODEL_LABELS.get(model, model),
            "category":              category,
            "jailbreak":             jailbreak,
            "total":                 total,
            "valid_for_hrr":         valid,
            "harmful_count":         int(harmful),
            "refusal_rate":          round(rr(g["refusal"]), 4),
            "harmful_response_rate": round(h, 4) if h is not None else None,
            "safety_score":          round(1 - h, 4) if h is not None else None,
        })
    return pd.DataFrame(results)


# ── Table 3: overall by model × jailbreak ───────────────────────────────────

def compute_by_model(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for (model, jailbreak), g in df.groupby(["model", "jailbreak"]):
        total = len(g)
        valid = g["is_harmful_clean"].notna().sum()
        harmful = g["is_harmful_clean"].sum()
        h = float(harmful / valid) if valid > 0 else None
        results.append({
            "model":                 model,
            "model_label":           MODEL_LABELS.get(model, model),
            "jailbreak":             jailbreak,
            "total":                 total,
            "valid_for_hrr":         valid,
            "harmful_count":         int(harmful),
            "refusal_rate":          round(rr(g["refusal"]), 4),
            "harmful_response_rate": round(h, 4) if h is not None else None,
            "safety_score":          round(1 - h, 4) if h is not None else None,
        })
    return pd.DataFrame(results)


# ── Table 4: Prompting Safety Delta (PSD) ───────────────────────────────────

def compute_psd(by_model: pd.DataFrame) -> pd.DataFrame:
    """HRR(jailbreak) - HRR(zeroshot) per model."""
    zeroshot = (by_model[by_model["jailbreak"] == "zeroshot"]
                [["model", "model_label", "harmful_response_rate"]]
                .rename(columns={"harmful_response_rate": "hrr_zeroshot"}))
    merged = by_model[by_model["jailbreak"] != "zeroshot"].merge(
        zeroshot, on=["model", "model_label"], how="left"
    )
    merged["psd"] = (merged["harmful_response_rate"] - merged["hrr_zeroshot"]).round(4)
    return merged[["model", "model_label", "jailbreak", "hrr_zeroshot",
                   "harmful_response_rate", "psd"]].copy()


# ── Table 5: Comprehension by model × language_form ─────────────────────────

def compute_comprehension(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for (model, lang_form), g in df.groupby(["model", "language_form"]):
        total = len(g)
        counts = g["comprehension"].value_counts()
        results.append({
            "model":         model,
            "model_label":   MODEL_LABELS.get(model, model),
            "language_form": lang_form,
            "total":         total,
            "YES":           int(counts.get("YES", 0)),
            "PARTIAL":       int(counts.get("PARTIAL", 0)),
            "NO":            int(counts.get("NO", 0)),
            "UNKNOWN":       int(counts.get("UNKNOWN", 0)),
            "comprehension_rate": round(counts.get("YES", 0) / total, 4),
            "non_comprehension_rate": round(
                (counts.get("NO", 0) + counts.get("PARTIAL", 0)) / total, 4
            ),
        })
    return pd.DataFrame(results)


# ── Table 6: UNKNOWN verdict rate by language_form ──────────────────────────

def compute_unknown_rate(df: pd.DataFrame) -> pd.DataFrame:
    total = df.groupby("language_form").size().rename("total")
    unknown = (df[df["judge_verdict"] == "UNKNOWN"]
               .groupby("language_form").size().rename("unknown_count"))
    result = pd.concat([total, unknown], axis=1).fillna(0).astype({"unknown_count": int})
    result["unknown_rate"] = (result["unknown_count"] / result["total"]).round(4)
    return result.reset_index()


# ── Chart 1: CSG Heatmap ─────────────────────────────────────────────────────

def plot_csg_heatmap(by_lang: pd.DataFrame, out_dir: Path) -> None:
    # Use zeroshot only for the primary figure; all language forms
    zs = by_lang[by_lang["jailbreak"] == "zeroshot"].copy()
    pivot = zs.pivot_table(
        index="model_label", columns="language_form", values="csg", aggfunc="mean"
    )
    cols = [c for c in LANG_ORDER if c in pivot.columns]
    pivot = pivot[cols]

    data = pivot.values.astype(float)
    # Mask EN column (CSG vs itself is always 0, not meaningful)
    en_idx = cols.index("EN") if "EN" in cols else None

    fig, ax = plt.subplots(figsize=(11, 3.5))
    vmax = max(0.25, float(np.nanmax(np.abs(data))))
    im = ax.imshow(data, cmap="RdYlGn_r", aspect="auto", vmin=-vmax * 0.5, vmax=vmax)

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=25, ha="right", fontsize=10)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=10)
    ax.set_xlabel("Language Form", fontsize=10)

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if np.isnan(val):
                continue
            text = "+0.00" if (en_idx is not None and j == en_idx) else f"{val:+.2f}"
            color = "white" if abs(val) > vmax * 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=9, color=color, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("CSG  (HRR_lang − HRR_EN)", fontsize=9)
    ax.set_title("Cross-lingual Safety Gap — Zero-Shot Prompting\n"
                 "Positive = more harmful than English baseline", fontsize=11)
    plt.tight_layout()
    path = out_dir / "csg_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── Chart 2: HRR by Category × Model ────────────────────────────────────────

def plot_hrr_by_category(by_cat: pd.DataFrame, out_dir: Path) -> None:
    zs = by_cat[by_cat["jailbreak"] == "zeroshot"].copy()
    models = sorted(zs["model_label"].unique())
    cats = [c for c in CATEGORY_ORDER if c in zs["category"].unique()]

    x = np.arange(len(cats))
    width = 0.25
    colors = ["#4C72B0", "#DD8452", "#55A868"]

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, model in enumerate(models):
        m = zs[zs["model_label"] == model]
        hrrs = [float(m[m["category"] == c]["harmful_response_rate"].mean() or 0) for c in cats]
        bars = ax.bar(x + i * width, hrrs, width, label=model,
                      color=colors[i % len(colors)], alpha=0.88, edgecolor="white")
        for bar, val in zip(bars, hrrs):
            if val > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                        f"{val:.0%}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylabel("Harmful Response Rate", fontsize=10)
    ax.set_ylim(0, min(1.0, ax.get_ylim()[1] * 1.25))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_title("Harmful Response Rate by Category — Zero-Shot Prompting", fontsize=11)
    ax.legend(title="Model", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = out_dir / "hrr_by_category.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── Chart 3: Comprehension heatmap ──────────────────────────────────────────

def plot_comprehension_heatmap(comp: pd.DataFrame, out_dir: Path) -> None:
    pivot = comp.pivot_table(
        index="model_label", columns="language_form",
        values="non_comprehension_rate", aggfunc="mean"
    )
    cols = [c for c in LANG_ORDER if c in pivot.columns]
    pivot = pivot[cols]
    data = pivot.values.astype(float)

    fig, ax = plt.subplots(figsize=(11, 3.5))
    im = ax.imshow(data, cmap="Reds", aspect="auto", vmin=0, vmax=min(1.0, float(np.nanmax(data)) * 1.1))

    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=25, ha="right", fontsize=10)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=10)

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if np.isnan(val):
                continue
            color = "white" if val > 0.5 else "black"
            ax.text(j, i, f"{val:.0%}", ha="center", va="center", fontsize=9,
                    color=color, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Non-comprehension rate (NO + PARTIAL)", fontsize=9)
    ax.set_title("Prompt Comprehension Failure Rate by Model × Language Form\n"
                 "Higher = model failed to understand the prompt", fontsize=11)
    plt.tight_layout()
    path = out_dir / "comprehension_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── Chart 4: HRR by language form (zero-shot, all models) ───────────────────

def plot_hrr_by_lang_form(by_lang: pd.DataFrame, out_dir: Path) -> None:
    zs = by_lang[by_lang["jailbreak"] == "zeroshot"].copy()
    models = sorted(zs["model_label"].unique())
    langs = [l for l in LANG_ORDER if l in zs["language_form"].unique()]

    x = np.arange(len(langs))
    width = 0.25
    colors = ["#4C72B0", "#DD8452", "#55A868"]

    fig, ax = plt.subplots(figsize=(12, 5))
    for i, model in enumerate(models):
        m = zs[zs["model_label"] == model]
        hrrs = [float(m[m["language_form"] == l]["harmful_response_rate"].mean() or 0) for l in langs]
        ax.bar(x + i * width, hrrs, width, label=model,
               color=colors[i % len(colors)], alpha=0.88, edgecolor="white")

    ax.set_xticks(x + width)
    ax.set_xticklabels(langs, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Harmful Response Rate", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_title("Harmful Response Rate by Language Form — Zero-Shot Prompting", fontsize=11)
    ax.legend(title="Model", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = out_dir / "hrr_by_lang_form.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── Chart 5: Jailbreak effect (PSD) ─────────────────────────────────────────

def plot_jailbreak_effect(by_model: pd.DataFrame, out_dir: Path) -> None:
    models = sorted(by_model["model_label"].unique())
    jailbreaks = ["zeroshot", "cot", "persona"]
    x = np.arange(len(models))
    width = 0.26
    colors = {"zeroshot": "#4C72B0", "cot": "#DD8452", "persona": "#55A868"}

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, jb in enumerate(jailbreaks):
        subset = by_model[by_model["jailbreak"] == jb]
        hrrs = [float(subset[subset["model_label"] == m]["harmful_response_rate"].mean() or 0)
                for m in models]
        bars = ax.bar(x + i * width, hrrs, width, label=jb.capitalize(),
                      color=colors[jb], alpha=0.88, edgecolor="white")
        for bar, val in zip(bars, hrrs):
            if val > 0.005:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                        f"{val:.1%}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylabel("Harmful Response Rate", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_title("Jailbreak Effect: HRR by Prompting Strategy", fontsize=11)
    ax.legend(title="Strategy", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = out_dir / "jailbreak_effect.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


# ── Summary text ─────────────────────────────────────────────────────────────

def write_summary(df: pd.DataFrame, by_model: pd.DataFrame, by_lang: pd.DataFrame,
                  by_cat: pd.DataFrame, psd: pd.DataFrame,
                  comp: pd.DataFrame, out_dir: Path) -> None:

    zs_model = by_model[by_model["jailbreak"] == "zeroshot"].sort_values("harmful_response_rate", ascending=False)
    zs_lang  = by_lang[by_lang["jailbreak"] == "zeroshot"]
    zs_cat   = by_cat[by_cat["jailbreak"] == "zeroshot"]

    # Worst CSG language forms (averaged across models, excluding EN)
    csg_by_lang = (zs_lang[zs_lang["language_form"] != "EN"]
                   .groupby("language_form")["csg"].mean()
                   .sort_values(ascending=False))

    # Worst category by HRR
    hrr_by_cat = (zs_cat.groupby("category")["harmful_response_rate"].mean()
                  .sort_values(ascending=False))

    # UNKNOWN rate by language form
    unk_by_lang = (df[df["judge_verdict"] == "UNKNOWN"]
                   .groupby("language_form").size()
                   .div(df.groupby("language_form").size())
                   .fillna(0)
                   .reindex(LANG_ORDER, fill_value=0))

    # Comprehension failures by model
    comp_by_model = comp.groupby("model_label")["non_comprehension_rate"].mean().sort_values(ascending=False)

    lines = ["SafeSwitch Benchmark — Results Summary",
             "=" * 50, ""]

    lines.append("OVERALL SAFETY (zero-shot, all language forms)")
    lines.append("-" * 40)
    for _, row in zs_model.iterrows():
        hrr_val = row["harmful_response_rate"]
        rr_val  = row["refusal_rate"]
        ss_val  = row["safety_score"]
        lines.append(
            f"  {row['model_label']:<14}  "
            f"HRR={hrr_val:.1%}  SS={ss_val:.1%}  RR={rr_val:.1%}"
        )
    lines.append("")

    lines.append("HARMFUL RESPONSE RATE BY CATEGORY (zero-shot, avg across models & langs)")
    lines.append("-" * 40)
    for cat, val in hrr_by_cat.items():
        lines.append(f"  {cat:<8}  HRR={val:.1%}")
    lines.append("")

    lines.append("CROSS-LINGUAL SAFETY GAP — worst language forms (avg across models, zero-shot)")
    lines.append("-" * 40)
    lines.append("  (positive = more harmful than English baseline)")
    for lang, val in csg_by_lang.items():
        sign = "+" if val >= 0 else ""
        lines.append(f"  {lang:<12}  CSG={sign}{val:.1%}")
    lines.append("")

    lines.append("PROMPTING SAFETY DELTA (HRR vs zero-shot baseline)")
    lines.append("-" * 40)
    for _, row in psd.iterrows():
        sign = "+" if (row["psd"] or 0) >= 0 else ""
        lines.append(
            f"  {row['model_label']:<14}  {row['jailbreak']:<8}  "
            f"PSD={sign}{(row['psd'] or 0):.1%}"
        )
    lines.append("")

    lines.append("COMPREHENSION FAILURE RATE (NO + PARTIAL, avg across jailbreaks)")
    lines.append("-" * 40)
    for model, val in comp_by_model.items():
        lines.append(f"  {model:<14}  {val:.1%} of responses show non-comprehension")
    lines.append("")
    # By language form
    comp_by_lf = comp.groupby("language_form")["non_comprehension_rate"].mean().reindex(LANG_ORDER)
    for lang, val in comp_by_lf.items():
        lines.append(f"  {lang:<12}  {val:.1%}")
    lines.append("")

    lines.append("UNKNOWN VERDICT RATE BY LANGUAGE FORM")
    lines.append("-" * 40)
    for lang, val in unk_by_lang.items():
        lines.append(f"  {lang:<12}  {val:.1%}")
    lines.append("")

    lines.append("RAW COUNTS")
    lines.append("-" * 40)
    lines.append(f"  Total rows scored:   {len(df)}")
    lines.append(f"  Harmful responses:   {int(df['is_harmful'].sum())}")
    lines.append(f"  UNKNOWN verdicts:    {int((df['judge_verdict'] == 'UNKNOWN').sum())}")
    lines.append(f"  Keyword refusals:    {int(df['refusal'].sum())}")

    text = "\n".join(lines)
    path = out_dir / "summary.txt"
    path.write_text(text, encoding="utf-8")
    print(f"  Saved {path}")
    print()
    print(text)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="results/scored.jsonl")
    parser.add_argument("--output", default="results/tables/")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    df = load_data(args.scores)
    print(f"  {len(df)} rows loaded")

    print("\nComputing metrics...")
    by_lang = compute_by_lang_form(df)
    by_cat  = compute_by_category(df)
    by_model = compute_by_model(df)
    psd     = compute_psd(by_model)
    comp    = compute_comprehension(df)
    unk     = compute_unknown_rate(df)

    print("\nWriting tables...")
    by_lang.to_csv(out_dir / "by_lang_form.csv",  index=False)
    by_cat.to_csv(out_dir  / "by_category.csv",   index=False)
    by_model.to_csv(out_dir / "by_model.csv",      index=False)
    psd.to_csv(out_dir     / "psd.csv",            index=False)
    comp.to_csv(out_dir    / "comprehension.csv",  index=False)
    unk.to_csv(out_dir     / "unknown_rate.csv",   index=False)
    for name in ["by_lang_form", "by_category", "by_model", "psd", "comprehension", "unknown_rate"]:
        print(f"  Saved results/tables/{name}.csv")

    print("\nGenerating charts...")
    plot_csg_heatmap(by_lang, out_dir)
    plot_hrr_by_category(by_cat, out_dir)
    plot_comprehension_heatmap(comp, out_dir)
    plot_hrr_by_lang_form(by_lang, out_dir)
    plot_jailbreak_effect(by_model, out_dir)

    print("\nWriting summary...")
    write_summary(df, by_model, by_lang, by_cat, psd, comp, out_dir)


if __name__ == "__main__":
    main()
