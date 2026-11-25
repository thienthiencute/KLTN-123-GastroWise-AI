"""
Automated Unit & Integration Tests for M7.2 Evaluation Framework.

Covers:
- Precision@K, Recall@K, NDCG@K, MAP@K
- Empty recommendations and empty ground truth
- Duplicate recommendations (must not inflate metrics)
- Graded relevance ordering sensitivity
- Dietary violation detection (vegetarian, non-spicy, halal)
- Cold-start evaluation (0 and 1 interactions vs >= 2 interactions)
- Deterministic evaluation results across repeated runs
- User scenarios (10/10) and Baseline vs M7.1 comparison integrity
"""

import math
import unittest

from evaluation.metrics.ranking_metrics import (
    average_precision_at_k,
    catalog_coverage,
    compute_summary_stats,
    dietary_constraint_violation_rate,
    intra_list_diversity,
    is_dietary_violation,
    mean_average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from evaluation.runners.compare_baselines import compare_baseline_vs_m7_1
from evaluation.runners.run_evaluation import evaluate_m7_1_profiles, evaluate_user_scenarios


class TestRankingMetrics(unittest.TestCase):
    def test_precision_and_recall_at_k(self):
        recs = ["a", "b", "c", "d", "e"]
        rel = ["a", "c", "f"]
        self.assertAlmostEqual(precision_at_k(recs, rel, 5), 2 / 5)
        self.assertAlmostEqual(recall_at_k(recs, rel, 5), 2 / 3)
        self.assertAlmostEqual(precision_at_k(recs, rel, 2), 1 / 2)
        self.assertAlmostEqual(recall_at_k(recs, rel, 2), 1 / 3)

    def test_ndcg_graded_relevance_and_ordering(self):
        grades = {"a": 3, "b": 1, "c": 0}
        ideal_recs = ["a", "b", "c"]
        suboptimal_recs = ["b", "a", "c"]
        self.assertAlmostEqual(ndcg_at_k(ideal_recs, grades, 3), 1.0)
        sub_ndcg = ndcg_at_k(suboptimal_recs, grades, 3)
        self.assertGreater(sub_ndcg, 0.0)
        self.assertLess(sub_ndcg, 1.0)

    def test_map_at_k(self):
        recs_u1 = ["a", "x", "b"]
        rel_u1 = ["a", "b"]
        # P@1 = 1.0, P@3 = 2/3 -> AP = (1.0 + 2/3) / 2 = 5/6
        self.assertAlmostEqual(average_precision_at_k(recs_u1, rel_u1, 3), 5 / 6)

        recs_u2 = ["x", "y"]
        rel_u2 = ["a"]
        self.assertAlmostEqual(mean_average_precision_at_k([recs_u1, recs_u2], [rel_u1, rel_u2], 3), (5 / 6 + 0.0) / 2)

    def test_empty_recommendations_and_empty_ground_truth(self):
        self.assertEqual(precision_at_k([], ["a"], 5), 0.0)
        self.assertEqual(recall_at_k([], ["a"], 5), 0.0)
        self.assertEqual(ndcg_at_k([], {"a": 3}, 5), 0.0)
        self.assertEqual(average_precision_at_k([], ["a"], 5), 0.0)

        self.assertEqual(precision_at_k(["a", "b"], [], 5), 0.0)
        self.assertEqual(recall_at_k(["a", "b"], [], 5), 0.0)
        self.assertEqual(ndcg_at_k(["a", "b"], {}, 5), 0.0)
        self.assertEqual(average_precision_at_k(["a", "b"], [], 5), 0.0)

    def test_duplicate_recommendations_do_not_inflate_scores(self):
        dup_recs = ["a", "a", "a", "b", "c"]
        rel = ["a", "d"]
        grades = {"a": 3, "d": 2}
        # Only first "a" should count as 1 hit, not 3
        self.assertAlmostEqual(precision_at_k(dup_recs, rel, 5), 1 / 5)
        self.assertAlmostEqual(recall_at_k(dup_recs, rel, 5), 1 / 2)
        self.assertLess(ndcg_at_k(dup_recs, grades, 5), 1.0)

    def test_dietary_violation_detection(self):
        self.assertFalse(is_dietary_violation("cơm chay thanh đạm", ["chay"]))
        self.assertTrue(is_dietary_violation("lẩu gà nấm rau củ", ["chay"]))
        self.assertTrue(is_dietary_violation("mì cay sa tế", ["không cay"]))
        self.assertFalse(is_dietary_violation("phở bò nước dùng", ["không cay"]))
        self.assertTrue(is_dietary_violation("cơm sườn", ["halal"]))

        items = [
            {"tags": "cơm chay vegan"},
            {"tags": "lẩu gà nấm thịt gà"},
        ]
        self.assertAlmostEqual(dietary_constraint_violation_rate(items, ["chay"]), 0.5)

    def test_coverage_ild_and_summary_stats(self):
        cov = catalog_coverage([["a", "b"], ["b", "c"]], ["a", "b", "c", "d"])
        self.assertAlmostEqual(cov, 0.75)

        ild = intra_list_diversity(["phở bò nóng", "chè ngọt mát"])
        self.assertAlmostEqual(ild, 1.0)

        stats = compute_summary_stats([0.5, 0.7, 0.9])
        self.assertEqual(stats["n"], 3)
        self.assertAlmostEqual(stats["mean"], 0.7)
        self.assertFalse(math.isnan(stats["std"]))


class TestEvaluationRunners(unittest.TestCase):
    def test_cold_start_and_determinism(self):
        res1 = evaluate_m7_1_profiles()
        res2 = evaluate_m7_1_profiles()
        self.assertEqual(res1["summary"], res2["summary"])
        self.assertEqual(res1["per_user"], res2["per_user"])

        # Verify cold-start vs warm CF cohorts exist and cold-start works
        self.assertGreater(res1["cold_vs_warm"]["cold_start"]["count"], 0)
        self.assertGreater(res1["cold_vs_warm"]["warm_cf"]["count"], 0)
        self.assertGreater(res1["cold_vs_warm"]["cold_start"]["ndcg@10_mean"], 0.5)

    def test_all_10_user_scenarios_pass(self):
        scenarios = evaluate_user_scenarios()
        self.assertEqual(len(scenarios), 10)
        for sc in scenarios:
            self.assertTrue(sc["passed"], f"Scenario failed: {sc}")

    def test_baseline_comparison_m7_1_improves_over_baseline(self):
        comp = compare_baseline_vs_m7_1()
        rows = {r["metric"]: r for r in comp["rows"]}
        self.assertGreaterEqual(rows["NDCG@5"]["m7_1"], rows["NDCG@5"]["baseline"])
        self.assertGreaterEqual(rows["NDCG@10"]["m7_1"], rows["NDCG@10"]["baseline"])
        self.assertGreaterEqual(rows["MAP@10"]["m7_1"], rows["MAP@10"]["baseline"])


if __name__ == "__main__":
    unittest.main()
