"""
Computes RR, HRR, Safety Score, and Cross-lingual Safety Gap from scored results.
Generates summary tables (CSV) and charts (PNG) in results/tables/.

Usage:
    python scripts/analyze.py --scores results/tables/scored.csv \
                              --prompts data/annotated/all_prompts_final.csv \
                              --output results/tables/
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def load_data(scores_path: str, prompts_path: str) -> pd.DataFrame:
    scores = pd.read_csv(scores_path)
    prompts = pd.read_csv(prompts_path)[["prompt_id", "category", "language_form"]]
    return scores.merge(prompts, on="prompt_id", how="left")


def compute_metrics(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Refusal Rate: keyword_refusal == True
    df["refused"] = df["keyword_refusal"].astype(bool)
    df["harmful"] = df["is_harmful"].astype(bool)

    group_cols = ["model", "category", "language_form", "technique"]

    agg = df.groupby(group_cols).agg(
        total=("prompt_id", "count"),
        refusals=("refused", "sum"),
        harmful_count=("harmful", "sum"),
    ).reset_index()

    agg["refusal_rate"] = agg["refusals"] / agg["total"]
    agg["harmful_response_rate"] = agg["harmful_count"] / agg["total"]
    agg["safety_score"] = 1 - agg["harmful_response_rate"]

    # Cross-lingual Safety Gap: HRR(lang) - HRR(EN)
    en_hrr = agg[agg["language_form"] == "EN"][
        ["model", "category", "technique", "harmful_response_rate"]
    ].rename(columns={"harmful_response_rate": "hrr_en"})

    agg = agg.merge(en_hrr, on=["model", "category", "technique"], how="left")
    agg["csg"] = agg["harmful_response_rate"] - agg["hrr_en"]

    return {
        "by_language_form": agg,
        "by_model": agg.groupby(["model", "technique"]).agg(
            refusal_rate=("refusal_rate", "mean"),
            harmful_response_rate=("harmful_response_rate", "mean"),
            safety_score=("safety_score", "mean"),
        ).reset_index(),
        "by_category": agg.groupby(["category", "language_form"]).agg(
            harmful_response_rate=("harmful_response_rate", "mean"),
            csg=("csg", "mean"),
        ).reset_index(),
    }


def plot_csg_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    pivot = df.pivot_table(
        index="model", columns="language_form", values="csg", aggfunc="mean"
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(pivot.values, cmap="RdYlGn_r", aspect="auto", vmin=-0.2, vmax=0.5)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    plt.colorbar(im, ax=ax, label="Cross-lingual Safety Gap (HRR delta vs EN)")
    ax.set_title("Cross-lingual Safety Gap by Model and Language Form")
    plt.tight_layout()
    out_path = output_dir / "csg_heatmap.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Compute benchmark metrics and generate charts.")
    parser.add_argument("--scores", default="results/tables/scored.csv")
    parser.add_argument("--prompts", default="data/annotated/all_prompts_final.csv")
    parser.add_argument("--output", default="results/tables/")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(args.scores, args.prompts)
    metrics = compute_metrics(df)

    for name, table in metrics.items():
        path = out_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        print(f"Saved {path}")

    plot_csg_heatmap(metrics["by_language_form"], out_dir)
    print("Analysis complete.")


if __name__ == "__main__":
    main()
