"""
Baseline vs. M7.1 Controlled Comparison Runner (M7.2).

Compares the reconstructed pre-M7.1 baseline (commit a17ccc3) against the M7.1
recommendation engine using identical user profiles, CF interactions, and
candidate pools.

Usage:
  python -m evaluation.runners.compare_baselines
"""

import json
import os
from typing import Any, Dict, List
from unittest.mock import patch

from app.core.collaborative_filter import CollaborativeFilteringEngine
from app.core.recommender import recommend_hybrid
from app.schemas.recommendation import HybridRecommendRequest
from evaluation.datasets.synthetic_benchmark import (
    DATASET_METADATA,
    build_baseline_naive_catalog_df,
    build_normalized_catalog_df,
    get_synthetic_cf_interactions,
    get_synthetic_user_profiles,
)
from evaluation.metrics.ranking_metrics import (
    catalog_coverage,
    compute_summary_stats,
    dietary_constraint_violation_rate,
    intra_list_diversity,
    mean_average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from evaluation.runners.baseline_recommender import recommend_hybrid_baseline
from evaluation.runners.run_evaluation import SEED, _set_deterministic_seed


def run_engine_evaluation(mode: str) -> Dict[str, Any]:
    """Run either 'baseline' or 'm7_1' on identical profiles & CF model."""
    _set_deterministic_seed(SEED)
    profiles = get_synthetic_user_profiles()
    interactions = get_synthetic_cf_interactions()

    cf = CollaborativeFilteringEngine(n_factors=4)
    cf.train_from_interactions(interactions)

    if mode == "baseline":
        catalog_df = build_baseline_naive_catalog_df()
    else:
        catalog_df = build_normalized_catalog_df()

    all_rec_ids: List[List[str]] = []
    all_rel_ids: List[List[str]] = []
    p5_list, r5_list, n5_list = [], [], []
    p10_list, r10_list, n10_list = [], [], []
    ild_list, viol_list = [], []

    for profile in profiles:
        req = HybridRecommendRequest(
            user_id=profile["user_id"],
            user_gps=profile["user_gps"],
            taste_vector=profile["taste_vector"],
            dietary_exclusions=profile["dietary_exclusions"],
            weather_type=profile["weather_type"],
            temperature=profile["temperature"],
            max_price=profile["max_price"],
            limit=10,
        )
        if mode == "baseline":
            res = recommend_hybrid_baseline(req, catalog_df, cf)
        else:
            with patch("app.core.recommender.get_dataset", return_value=catalog_df), \
                 patch("app.core.recommender.cf_engine", cf):
                res = recommend_hybrid(req)

        rec_ids = [it.id for it in res.items]
        rec_dicts = [{"id": it.id, "tags": it.tags} for it in res.items]
        grades = profile["relevance_grades"]
        rel_ids = [rid for rid, g in grades.items() if g > 0]

        all_rec_ids.append(rec_ids)
        all_rel_ids.append(rel_ids)

        p5_list.append(precision_at_k(rec_ids, rel_ids, 5))
        r5_list.append(recall_at_k(rec_ids, rel_ids, 5))
        n5_list.append(ndcg_at_k(rec_ids, grades, 5))
        p10_list.append(precision_at_k(rec_ids, rel_ids, 10))
        r10_list.append(recall_at_k(rec_ids, rel_ids, 10))
        n10_list.append(ndcg_at_k(rec_ids, grades, 10))
        ild_list.append(intra_list_diversity([it.tags for it in res.items]))
        viol_list.append(dietary_constraint_violation_rate(rec_dicts, profile["dietary_exclusions"]))

    unique_catalog = catalog_df.drop_duplicates(subset=["name", "address"], keep="first")
    return {
        "Precision@5": compute_summary_stats(p5_list)["mean"],
        "Recall@5": compute_summary_stats(r5_list)["mean"],
        "NDCG@5": compute_summary_stats(n5_list)["mean"],
        "Precision@10": compute_summary_stats(p10_list)["mean"],
        "Recall@10": compute_summary_stats(r10_list)["mean"],
        "NDCG@10": compute_summary_stats(n10_list)["mean"],
        "MAP@10": round(mean_average_precision_at_k(all_rec_ids, all_rel_ids, 10), 4),
        "Catalog Coverage": round(catalog_coverage(all_rec_ids, unique_catalog["id"].tolist()), 4),
        "Intra-list Diversity": compute_summary_stats(ild_list)["mean"],
        "Dietary Violation Rate": compute_summary_stats(viol_list)["mean"],
    }


def compare_baseline_vs_m7_1() -> Dict[str, Any]:
    baseline_metrics = run_engine_evaluation("baseline")
    m7_1_metrics = run_engine_evaluation("m7_1")

    comparison_rows = []
    for key in baseline_metrics:
        b_val = baseline_metrics[key]
        m_val = m7_1_metrics[key]
        diff = round(m_val - b_val, 4)
        comparison_rows.append({
            "metric": key,
            "baseline": b_val,
            "m7_1": m_val,
            "improvement": diff,
        })
    return {
        "dataset": DATASET_METADATA["name"],
        "is_synthetic": True,
        "seed": SEED,
        "rows": comparison_rows,
    }


def main() -> None:
    report_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_dir, exist_ok=True)

    comparison = compare_baseline_vs_m7_1()
    md_lines = [
        "# Baseline vs. M7.1 Recommendation Comparison (Synthetic Benchmark)",
        "",
        "| Metric | Baseline | M7.1 | Improvement |",
        "|---|---:|---:|---:|",
    ]
    for row in comparison["rows"]:
        sign = "+" if row["improvement"] > 0 else ""
        md_lines.append(
            f"| {row['metric']} | {row['baseline']:.4f} | {row['m7_1']:.4f} | {sign}{row['improvement']:.4f} |"
        )

    md_path = os.path.join(report_dir, "latest_comparison.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    json_path = os.path.join(report_dir, "latest_comparison.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    print("\n".join(md_lines))
    print(f"\nSaved comparison report to: {md_path}")


if __name__ == "__main__":
    main()
