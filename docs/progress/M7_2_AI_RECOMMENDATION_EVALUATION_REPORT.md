# M7.2 — AI Recommendation Evaluation & Benchmarking Report

- **Target Repository:** `thienthiencute/KLTN-123-GastroWise-AI`
- **Branch:** `feature/m7-2-ai-recommendation-evaluation` (branched from M7.1 commit `f4b0e176dcb838adf5ce8e6dcd6e1da9de154e88`)
- **Final Verdict:** **`CONDITIONAL PASS — DATA LIMITATIONS`** *(all offline metrics, scenarios, and 34/34 unit tests pass deterministically; evaluation uses clearly labeled synthetic fixtures because production user interaction logs are unavailable offline)*

---

## 1. Evaluation Objectives

The M7.2 offline evaluation framework independently measures:
1. Whether recommended restaurants are relevant to user preferences (`Precision@K`, `Recall@K`, `MAP@K`).
2. Whether highly relevant restaurants are ranked near the top (`NDCG@K`).
3. Whether hard dietary and budget constraints are strictly enforced (`Dietary Violation Rate`).
4. Whether cold-start users (`0` or `< 2` interactions) receive relevant recommendations alongside warm CF users (`>= 2` interactions).
5. Whether the M7.1 recommendation engine improves over the reconstructed pre-M7.1 baseline (`a17ccc3`) under identical evaluation conditions.

---

## 2. Dataset Design & Source

- **Source:** Synthetic evaluation fixture (`evaluation/datasets/synthetic_benchmark.py`, `DATASET_METADATA["is_synthetic"] = True`, fixed `SEED = 42`).
- **Catalog:** 22 raw restaurant records (20 unique `(name, address)` restaurants + 2 duplicate records with distinct IDs) spanning Ho Chi Minh City districts, including:
  - Foody 10-point crawled ratings (`3.8/10` to `9.4/10`, including `<= 5.0` poor Foody ratings `3.8/10` and `4.0/10` with Foody subscores and `reviewsCount = 0`).
  - GastroWise 5-star user-reviewed ratings (`4.1/5` to `4.8/5` with `reviewsCount > 0`).
  - Vegetarian (`chay`/`vegan`), non-vegetarian meat+mushroom trap (`Lẩu Gà Nấm Phú Yên`), Halal, spicy, sweet, sour, budget (`25k–50k VND`), and upscale (`450k VND`) restaurants.
- **User Profiles:** 10 diverse synthetic profiles (`u_warm_spicy`, `u_veg_strict`, `u_budget_tight`, `u_gps_nearby`, `u_multi_taste`, `u_cold_zero`, `u_low_hist`, `u_warm_sweet`, `u_non_spicy`, `u_halal_user`) with graded relevance labels (`3` = highly relevant, `2` = relevant, `1` = marginally relevant, `0` = irrelevant).
- **CF Interactions:** 12 synthetic interaction records (`VIEW`, `CLICK`, `SAVE`, `FAVORITE`, `REVIEW`) yielding 2 warm CF users (`>= 2` interactions) and 8 cold-start users (`0` or `1` interaction).

---

## 3. Dataset Limitations

- **Synthetic Ground Truth:** Relevance grades and interaction logs are synthetic fixtures rather than production user clicks, orders, or reviews. High offline scores on synthetic data do **not** prove production quality on real user traffic.
- **Sample Size:** $N = 10$ user profiles and 20 unique restaurants; 95% confidence intervals are descriptive (`1.96 * SE`) and no formal hypothesis test of statistical significance is claimed.
- **Offline Scope:** MongoDB Atlas is not queried during offline CI evaluation; production catalog scale and noise require staging validation.

---

## 4. Metric Definitions

Implemented independently in `evaluation/metrics/ranking_metrics.py`:

- **Precision@K:** $\frac{|\text{unique}(\text{Rec}_{1..K}) \cap \text{Rel}|}{K}$ (`0.0` if $K \le 0$ or empty). Duplicate IDs are credited at most once.
- **Recall@K:** $\frac{|\text{unique}(\text{Rec}_{1..K}) \cap \text{Rel}|}{|\text{Rel}|}$ (`0.0` if empty ground truth or empty recommendations).
- **NDCG@K:** $\frac{\text{DCG}@K}{\text{IDCG}@K}$ where $\text{DCG}@K = \sum_{i=1}^{\min(K, |\text{Rec}|)} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$ (unique first occurrence only).
- **MAP@K:** Mean across users of $\text{AP}@K = \frac{1}{\min(|\text{Rel}|, K)} \sum_{i=1}^{\min(K, |\text{Rec}|)} P@i \cdot \mathbb{I}[\text{item}_i \in \text{Rel} \text{ and unseen}]$.
- **Catalog Coverage:** $\frac{|\bigcup_{u} \text{Rec}_u \cap \text{Catalog}|}{|\text{Catalog}|}$.
- **Intra-list Diversity (ILD):** Mean pairwise Jaccard distance $1 - \frac{|T_i \cap T_j|}{|T_i \cup T_j|}$ over restaurant tag tokens.
- **Dietary Constraint Violation Rate:** Fraction of recommended items violating requested `dietary_exclusions`.

---

## 5. Baseline Methodology

`evaluation/runners/baseline_recommender.py` reconstructs the pre-M7.1 recommender (`a17ccc3`) from git diff inspection:
- Naive rating normalization (`r / 2.0 if r > 5.0 else r`), leaving poor Foody ratings $\le 5.0$ unscaled.
- Non-strict dietary filter (`chay|vegan|vegetarian|nấm|rau củ` with `if mask.any():` fallback).
- No `(name, address)` candidate-pool deduplication before `head(limit)`.
- No normalized rating quality bonus (`rating_bonus = 0.0`) and single-key sorting without tie-breakers.

Both Baseline and M7.1 were executed on identical user profiles, CF interactions, and candidate pools (`python -m evaluation.runners.compare_baselines`).

---

## 6. Evaluation Results

### 6.1 Baseline vs. M7.1 Comparison

| Metric | Baseline | M7.1 | Improvement |
|---|---:|---:|---:|
| Precision@5 | 0.4600 | 0.4800 | +0.0200 |
| Recall@5 | 0.6283 | 0.6483 | +0.0200 |
| NDCG@5 | 0.7265 | 0.8232 | +0.0967 |
| Precision@10 | 0.3400 | 0.3800 | +0.0400 |
| Recall@10 | 0.8700 | 0.9550 | +0.0850 |
| NDCG@10 | 0.7930 | 0.9161 | +0.1231 |
| MAP@10 | 0.6580 | 0.7781 | +0.1201 |
| Catalog Coverage | 0.9000 | 0.9000 | 0.0000 |
| Intra-list Diversity | 0.7650 | 0.7801 | +0.0151 |
| Dietary Violation Rate | 0.0000 | 0.0000 | 0.0000 |

### 6.2 M7.1 Statistical Summary ($N = 10$ Synthetic Profiles, Seed = 42)

| Metric | Mean | Std Dev | Variance | 95% CI (Normal Approx.) |
|---|---:|---:|---:|---|
| Precision@5 | 0.4800 | 0.1687 | 0.0284 | [0.3755, 0.5845] |
| Recall@5 | 0.6483 | 0.2181 | 0.0476 | [0.5132, 0.7835] |
| NDCG@5 | 0.8231 | 0.1315 | 0.0173 | [0.7416, 0.9046] |
| Precision@10 | 0.3800 | 0.1398 | 0.0196 | [0.2933, 0.4667] |
| Recall@10 | 0.9550 | 0.0956 | 0.0091 | [0.8957, 1.0000] |
| NDCG@10 | 0.9161 | 0.0669 | 0.0045 | [0.8747, 0.9576] |

---

## 7. User Scenario Results (10/10 PASS)

1. **User prefers spicy food:** PASS — `Lẩu Thái Khun Thai` ranked #1 (`score=0.9441`).
2. **User prefers vegetarian food:** PASS — Returned 3 vegetarian items, `violation_rate=0.0`, excluded `Lẩu Gà Nấm Phú Yên`.
3. **User has strict maximum budget ($\le 50,000$ VND):** PASS — Returned 8 items, max returned price `50000`.
4. **User wants restaurants near GPS location:** PASS — Max distance in top-5 was `0.33 km`.
5. **User has multiple taste preferences:** PASS — `Chè Khúc Bạch Thanh` ranked #1 (`taste_score=0.852`).
6. **User has no historical interactions (0):** PASS — `is_cold_start=True`, `w2_cf=0.0`, returned relevant items via Taste DNA + Weather.
7. **User has fewer than two interactions (1):** PASS — `is_cold_start=True`, `w2_cf=0.0`.
8. **User has sufficient CF history ($\ge 2$):** PASS — `is_cold_start=False`, `w2_cf=0.30`, `top_cf_score=0.741`.
9. **No restaurant satisfies all hard constraints:** PASS — Safely returned `total=0, items=[]`.
10. **Dataset contains missing or invalid values:** PASS — Handled `NaN` rating/price/coordinates cleanly (`price=50000, distance_km=999.0`).

---

## 8. Cold-Start Analysis

| Cohort | Users ($n$) | Mean NDCG@5 | Mean NDCG@10 | Mean Recall@10 |
|---|---:|---:|---:|---:|
| Cold-Start (`0` or `1` interaction) | 8 | 0.8023 | 0.9050 | 0.9750 |
| Warm CF (`>= 2` interactions) | 2 | 0.9066 | 0.9607 | 0.8750 |

- Cold-start users (`w1_taste=0.65, w2_cf=0.0, w3_env=0.35`) maintain strong top-10 ranking (`NDCG@10 = 0.9050`) using 6-D Taste DNA, weather context, and normalized rating quality prior.
- Warm CF users (`w1_taste=0.45, w2_cf=0.30, w3_env=0.25`) achieve higher top-5 ranking precision (`NDCG@5 = 0.9066` vs. `0.8023`).

---

## 9. Verification Commands & Test Results

```bash
.venv/bin/python -m evaluation.runners.run_evaluation
.venv/bin/python -m evaluation.runners.compare_baselines
.venv/bin/python -m unittest discover -p "test_*.py" -v
```
- **Unit & Integration Test Suite:** **34 passed / 0 failed / 0 skipped** (`2.551s`), including 10 new tests in `evaluation/tests/test_evaluation_metrics.py`, 17 in `test_m7_recommender_quality.py`, 4 in `test_internal_auth.py`, and 3 in `test_routing_contract.py`.

---

## 10. Recommendations for Future Improvement

1. Collect anonymized real user impression/click/review logs in staging to replace synthetic relevance fixtures and enable statistical significance testing (paired t-test / Wilcoxon signed-rank).
2. Add online A/B telemetry (CTR, conversion-to-itinerary, and dwell time) in Core Service.
3. Expand TF-IDF tag synonyms and multi-criteria rating weights (quality vs. price vs. location).
