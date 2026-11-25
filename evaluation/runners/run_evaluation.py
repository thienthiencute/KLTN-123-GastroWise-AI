"""
Reproducible Offline Evaluation & Scenario Runner for GastroWise M7.1 Recommender.

Usage:
  python -m evaluation.runners.run_evaluation
"""

import json
import os
import random
from typing import Any, Dict, List
from unittest.mock import patch
import numpy as np
import pandas as pd

from app.core.collaborative_filter import CollaborativeFilteringEngine
from app.core.recommender import recommend_hybrid
from app.schemas.recommendation import HybridRecommendRequest
from evaluation.datasets.synthetic_benchmark import (
    DATASET_METADATA,
    build_normalized_catalog_df,
    get_synthetic_cf_interactions,
    get_synthetic_user_profiles,
)
from evaluation.metrics.ranking_metrics import (
    average_precision_at_k,
    catalog_coverage,
    compute_summary_stats,
    dietary_constraint_violation_rate,
    intra_list_diversity,
    mean_average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

SEED = 42


def _set_deterministic_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)


def evaluate_m7_1_profiles(k_values: List[int] = [5, 10]) -> Dict[str, Any]:
    """Evaluate M7.1 recommend_hybrid across all synthetic user profiles."""
    _set_deterministic_seed(SEED)
    catalog_df = build_normalized_catalog_df()
    profiles = get_synthetic_user_profiles()
    interactions = get_synthetic_cf_interactions()

    cf = CollaborativeFilteringEngine(n_factors=4)
    cf.train_from_interactions(interactions)

    per_user_results: List[Dict[str, Any]] = []
    all_recommended_ids: List[List[str]] = []
    all_relevant_ids: List[List[str]] = []
    ild_values: List[float] = []
    violation_rates: List[float] = []

    with patch("app.core.recommender.get_dataset", return_value=catalog_df), \
         patch("app.core.recommender.cf_engine", cf):
        for profile in profiles:
            req = HybridRecommendRequest(
                user_id=profile["user_id"],
                user_gps=profile["user_gps"],
                taste_vector=profile["taste_vector"],
                dietary_exclusions=profile["dietary_exclusions"],
                weather_type=profile["weather_type"],
                temperature=profile["temperature"],
                max_price=profile["max_price"],
                limit=max(k_values),
            )
            res = recommend_hybrid(req)
            rec_ids = [item.id for item in res.items]
            rec_dicts = [{"id": it.id, "tags": it.tags, "price": it.price} for it in res.items]
            grades = profile["relevance_grades"]
            relevant_ids = [rid for rid, g in grades.items() if g > 0]

            all_recommended_ids.append(rec_ids)
            all_relevant_ids.append(relevant_ids)

            ild = intra_list_diversity([it.tags for it in res.items])
            v_rate = dietary_constraint_violation_rate(rec_dicts, profile["dietary_exclusions"])
            ild_values.append(ild)
            violation_rates.append(v_rate)

            user_metrics: Dict[str, Any] = {
                "user_id": profile["user_id"],
                "label": profile["label"],
                "is_cold_start": res.is_cold_start,
                "returned_count": len(rec_ids),
                "recommended_ids": rec_ids,
                "relevant_ids": relevant_ids,
                "precision@5": round(precision_at_k(rec_ids, relevant_ids, 5), 4),
                "recall@5": round(recall_at_k(rec_ids, relevant_ids, 5), 4),
                "ndcg@5": round(ndcg_at_k(rec_ids, grades, 5), 4),
                "precision@10": round(precision_at_k(rec_ids, relevant_ids, 10), 4),
                "recall@10": round(recall_at_k(rec_ids, relevant_ids, 10), 4),
                "ndcg@10": round(ndcg_at_k(rec_ids, grades, 10), 4),
                "ap@10": round(average_precision_at_k(rec_ids, relevant_ids, 10), 4),
                "ild": round(ild, 4),
                "dietary_violation_rate": round(v_rate, 4),
            }
            per_user_results.append(user_metrics)

    # Deduplicated unique catalog IDs (same (name, address) collapsed)
    unique_catalog = catalog_df.drop_duplicates(subset=["name", "address"], keep="first")
    coverage = catalog_coverage(all_recommended_ids, unique_catalog["id"].tolist())
    map_10 = mean_average_precision_at_k(all_recommended_ids, all_relevant_ids, 10)

    summary = {
        "precision@5": compute_summary_stats([u["precision@5"] for u in per_user_results]),
        "recall@5": compute_summary_stats([u["recall@5"] for u in per_user_results]),
        "ndcg@5": compute_summary_stats([u["ndcg@5"] for u in per_user_results]),
        "precision@10": compute_summary_stats([u["precision@10"] for u in per_user_results]),
        "recall@10": compute_summary_stats([u["recall@10"] for u in per_user_results]),
        "ndcg@10": compute_summary_stats([u["ndcg@10"] for u in per_user_results]),
        "map@10": round(map_10, 4),
        "catalog_coverage": round(coverage, 4),
        "intra_list_diversity": compute_summary_stats(ild_values),
        "dietary_violation_rate": compute_summary_stats(violation_rates),
    }

    cold_users = [u for u in per_user_results if u["is_cold_start"]]
    warm_users = [u for u in per_user_results if not u["is_cold_start"]]
    cold_vs_warm = {
        "cold_start": {
            "count": len(cold_users),
            "ndcg@5_mean": compute_summary_stats([u["ndcg@5"] for u in cold_users])["mean"],
            "ndcg@10_mean": compute_summary_stats([u["ndcg@10"] for u in cold_users])["mean"],
            "recall@10_mean": compute_summary_stats([u["recall@10"] for u in cold_users])["mean"],
        },
        "warm_cf": {
            "count": len(warm_users),
            "ndcg@5_mean": compute_summary_stats([u["ndcg@5"] for u in warm_users])["mean"],
            "ndcg@10_mean": compute_summary_stats([u["ndcg@10"] for u in warm_users])["mean"],
            "recall@10_mean": compute_summary_stats([u["recall@10"] for u in warm_users])["mean"],
        },
    }

    return {
        "dataset": DATASET_METADATA,
        "seed": SEED,
        "summary": summary,
        "cold_vs_warm": cold_vs_warm,
        "per_user": per_user_results,
    }


def evaluate_user_scenarios() -> List[Dict[str, Any]]:
    """Execute all 10 required user scenarios and report each separately."""
    _set_deterministic_seed(SEED)
    catalog_df = build_normalized_catalog_df()
    interactions = get_synthetic_cf_interactions()
    cf = CollaborativeFilteringEngine(n_factors=4)
    cf.train_from_interactions(interactions)

    scenarios: List[Dict[str, Any]] = []

    with patch("app.core.recommender.get_dataset", return_value=catalog_df), \
         patch("app.core.recommender.cf_engine", cf):
        # 1. User prefers spicy food
        r1 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_warm_spicy", user_gps=[10.7769, 106.7009],
            taste_vector=[0.95, 0.1, 0.2, 0.3, 0.5, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "1. User prefers spicy food",
            "passed": len(r1.items) > 0 and any("cay" in it.tags.lower() for it in r1.items[:2]),
            "top_3": [it.id for it in r1.items[:3]],
            "details": f"Top item: {r1.items[0].name if r1.items else 'None'} (score={r1.items[0].score if r1.items else 0})",
        })

        # 2. User prefers vegetarian food
        r2 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_veg_strict", user_gps=[10.7769, 106.7009],
            dietary_exclusions=["chay"], limit=5
        ))
        v2 = dietary_constraint_violation_rate(
            [{"tags": it.tags} for it in r2.items], ["chay"]
        )
        scenarios.append({
            "scenario": "2. User prefers vegetarian food",
            "passed": len(r2.items) > 0 and v2 == 0.0 and "r_meat_mushroom" not in [it.id for it in r2.items],
            "top_3": [it.id for it in r2.items[:3]],
            "details": f"Returned {len(r2.items)} vegetarian items, violation_rate={v2}",
        })

        # 3. User has strict maximum budget
        r3 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_budget_tight", user_gps=[10.7769, 106.7009],
            max_price=50000, limit=10
        ))
        all_under_budget = all(it.price <= 50000 for it in r3.items)
        scenarios.append({
            "scenario": "3. User has strict maximum budget (<= 50,000 VND)",
            "passed": len(r3.items) > 0 and all_under_budget,
            "top_3": [it.id for it in r3.items[:3]],
            "details": f"Returned {len(r3.items)} items, max returned price={max((it.price for it in r3.items), default=0)}",
        })

        # 4. User wants restaurants near GPS location
        r4 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_gps_nearby", user_gps=[10.7768, 106.7010],
            taste_vector=[0.2, 0.1, 0.1, 0.4, 0.9, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "4. User wants restaurants near GPS location",
            "passed": len(r4.items) > 0 and all(it.distance_km <= 5.0 for it in r4.items),
            "top_3": [it.id for it in r4.items[:3]],
            "details": f"Max distance in top-5: {max((it.distance_km for it in r4.items), default=0)} km",
        })

        # 5. User has multiple taste preferences (sweet + sour)
        r5 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_multi_taste", user_gps=[10.7769, 106.7009],
            taste_vector=[0.2, 0.85, 0.85, 0.2, 0.3, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "5. User has multiple taste preferences",
            "passed": len(r5.items) > 0,
            "top_3": [it.id for it in r5.items[:3]],
            "details": f"Top item: {r5.items[0].name if r5.items else 'None'} (taste_score={r5.items[0].taste_score if r5.items else 0})",
        })

        # 6. User has no historical interactions (0 interactions)
        r6 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_cold_zero", user_gps=[10.7769, 106.7009],
            taste_vector=[0.2, 0.1, 0.1, 0.5, 0.9, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "6. User has no historical interactions (0)",
            "passed": r6.is_cold_start is True and r6.applied_weights.get("w2_cf") == 0.0 and len(r6.items) > 0,
            "top_3": [it.id for it in r6.items[:3]],
            "details": f"is_cold_start={r6.is_cold_start}, weights={r6.applied_weights}",
        })

        # 7. User has fewer than two interactions (1 interaction)
        r7 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_low_hist", user_gps=[10.7769, 106.7009],
            taste_vector=[0.1, 0.2, 0.2, 0.4, 0.85, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "7. User has fewer than two interactions (1)",
            "passed": r7.is_cold_start is True and r7.applied_weights.get("w2_cf") == 0.0 and len(r7.items) > 0,
            "top_3": [it.id for it in r7.items[:3]],
            "details": f"is_cold_start={r7.is_cold_start}, weights={r7.applied_weights}",
        })

        # 8. User has sufficient collaborative-filtering history (>= 2)
        r8 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_warm_spicy", user_gps=[10.7769, 106.7009],
            taste_vector=[0.95, 0.1, 0.3, 0.3, 0.6, 0.1], limit=5
        ))
        scenarios.append({
            "scenario": "8. User has sufficient CF history (>= 2)",
            "passed": r8.is_cold_start is False and r8.applied_weights.get("w2_cf") == 0.30 and any(it.cf_score > 0 for it in r8.items),
            "top_3": [it.id for it in r8.items[:3]],
            "details": f"is_cold_start={r8.is_cold_start}, top_cf_score={r8.items[0].cf_score if r8.items else 0}",
        })

        # 9. No restaurant satisfies all hard constraints
        r9 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_veg_strict", dietary_exclusions=["chay", "halal"],
            max_price=1000, limit=5
        ))
        scenarios.append({
            "scenario": "9. No restaurant satisfies all hard constraints",
            "passed": r9.total == 0 and len(r9.items) == 0,
            "top_3": [],
            "details": f"total={r9.total}, items={len(r9.items)}",
        })

    # 10. Dataset contains missing or invalid values
    nan_df = pd.DataFrame([
        {
            "id": "r_nan_1",
            "name": "Quán Thiếu Dữ Liệu",
            "tags": "cơm tấm nước mắm",
            "rating": float("nan"),
            "price": float("nan"),
            "lat": float("nan"),
            "lon": float("nan"),
            "address": None,
            "district": None,
        }
    ])
    with patch("app.core.recommender.get_dataset", return_value=nan_df), \
         patch("app.core.recommender.cf_engine", cf):
        r10 = recommend_hybrid(HybridRecommendRequest(
            user_id="u_cold_zero", user_gps=[10.7769, 106.7009], limit=5
        ))
        scenarios.append({
            "scenario": "10. Dataset contains missing or invalid values",
            "passed": len(r10.items) == 1 and r10.items[0].distance_km == 999.0 and r10.items[0].price == 50000,
            "top_3": [it.id for it in r10.items],
            "details": f"price={r10.items[0].price}, distance_km={r10.items[0].distance_km}, score={r10.items[0].score}",
        })

    return scenarios


def main() -> None:
    report_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_dir, exist_ok=True)

    eval_data = evaluate_m7_1_profiles()
    scenarios = evaluate_user_scenarios()
    output = {
        "evaluation": eval_data,
        "scenarios": scenarios,
    }

    out_path = os.path.join(report_dir, "latest_evaluation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("=== M7.2 OFFLINE EVALUATION SUMMARY ===")
    for metric in ("precision@5", "recall@5", "ndcg@5", "precision@10", "recall@10", "ndcg@10"):
        stats = eval_data["summary"][metric]
        print(f"  {metric:14s}: mean={stats['mean']:.4f} +/- std={stats['std']:.4f} (95% CI [{stats['ci_95_low']:.4f}, {stats['ci_95_high']:.4f}])")
    print(f"  {'map@10':14s}: {eval_data['summary']['map@10']:.4f}")
    print(f"  {'coverage':14s}: {eval_data['summary']['catalog_coverage']:.4f}")
    print(f"  {'ild':14s}: {eval_data['summary']['intra_list_diversity']['mean']:.4f}")
    print(f"  {'diet_violation':14s}: {eval_data['summary']['dietary_violation_rate']['mean']:.4f}")
    print("\n=== USER SCENARIOS (10/10) ===")
    for sc in scenarios:
        status = "PASS" if sc["passed"] else "FAIL"
        print(f"  [{status}] {sc['scenario']} -> {sc['details']}")
    print(f"\nSaved JSON report to: {out_path}")


if __name__ == "__main__":
    main()
