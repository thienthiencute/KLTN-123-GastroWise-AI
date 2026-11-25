"""
Information Retrieval & Recommendation Quality Metrics for GastroWise (M7.2).

All metrics handle edge cases explicitly:
- k <= 0 -> 0.0
- Empty recommendations -> 0.0
- Empty ground truth -> 0.0
- Duplicate recommended IDs -> only the first occurrence receives relevance credit,
  preventing score inflation from duplicate restaurant entries.
"""

import math
from typing import Dict, Iterable, List, Optional, Sequence, Set


def precision_at_k(
    recommended_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """
    Precision@K = |unique(recommended[:k]) intersect relevant| / k
    Returns 0.0 if k <= 0 or recommended_ids is empty.
    """
    if k <= 0 or not recommended_ids:
        return 0.0
    rel_set = set(relevant_ids)
    if not rel_set:
        return 0.0

    top_k = list(recommended_ids)[:k]
    seen: Set[str] = set()
    hits = 0
    for item_id in top_k:
        if item_id not in seen:
            seen.add(item_id)
            if item_id in rel_set:
                hits += 1
    return hits / float(k)


def recall_at_k(
    recommended_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """
    Recall@K = |unique(recommended[:k]) intersect relevant| / |relevant|
    Returns 0.0 if k <= 0, recommended_ids is empty, or relevant_ids is empty.
    """
    if k <= 0 or not recommended_ids:
        return 0.0
    rel_set = set(relevant_ids)
    if not rel_set:
        return 0.0

    top_k = list(recommended_ids)[:k]
    seen = set(top_k)
    hits = len(seen.intersection(rel_set))
    return hits / float(len(rel_set))


def ndcg_at_k(
    recommended_ids: Sequence[str],
    relevance_grades: Dict[str, float],
    k: int,
) -> float:
    """
    Normalized Discounted Cumulative Gain (NDCG@K) with exponential gain:
      DCG@K = sum_{i=1..min(k, len(rec))} (2^{rel_i} - 1) / log2(i + 1)
      IDCG@K = max possible DCG@K from ideal descending sort of relevance_grades
      NDCG@K = DCG@K / IDCG@K (0.0 if IDCG@K == 0)
    Duplicate IDs in recommended_ids only receive credit on their first appearance.
    """
    if k <= 0 or not recommended_ids or not relevance_grades:
        return 0.0

    top_k = list(recommended_ids)[:k]
    dcg = 0.0
    seen: Set[str] = set()
    for idx, item_id in enumerate(top_k, start=1):
        if item_id in seen:
            continue
        seen.add(item_id)
        rel = max(0.0, float(relevance_grades.get(item_id, 0.0)))
        if rel > 0.0:
            dcg += (2.0 ** rel - 1.0) / math.log2(idx + 1)

    ideal_grades = sorted(
        (max(0.0, float(g)) for g in relevance_grades.values() if float(g) > 0.0),
        reverse=True,
    )[:k]
    if not ideal_grades:
        return 0.0

    idcg = sum(
        (2.0 ** rel - 1.0) / math.log2(idx + 1)
        for idx, rel in enumerate(ideal_grades, start=1)
    )
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def average_precision_at_k(
    recommended_ids: Sequence[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """
    Average Precision at K (AP@K):
      AP@K = (1 / min(|relevant|, k)) * sum_{i=1..min(k, len(rec))} P@i * rel(i)
    where rel(i) = 1 iff recommended[i-1] is relevant and not previously seen.
    """
    if k <= 0 or not recommended_ids:
        return 0.0
    rel_set = set(relevant_ids)
    if not rel_set:
        return 0.0

    top_k = list(recommended_ids)[:k]
    seen: Set[str] = set()
    hits = 0
    precision_sum = 0.0
    for idx, item_id in enumerate(top_k, start=1):
        if item_id not in seen:
            seen.add(item_id)
            if item_id in rel_set:
                hits += 1
                precision_sum += hits / float(idx)

    denom = float(min(len(rel_set), k))
    return precision_sum / denom if denom > 0.0 else 0.0


def mean_average_precision_at_k(
    per_user_recommended: Sequence[Sequence[str]],
    per_user_relevant: Sequence[Iterable[str]],
    k: int,
) -> float:
    """Mean Average Precision at K (MAP@K) across users."""
    if not per_user_recommended or len(per_user_recommended) != len(per_user_relevant):
        return 0.0
    aps = [
        average_precision_at_k(rec, rel, k)
        for rec, rel in zip(per_user_recommended, per_user_relevant)
    ]
    return sum(aps) / float(len(aps)) if aps else 0.0


def catalog_coverage(
    all_recommended_ids: Sequence[Sequence[str]],
    catalog_ids: Iterable[str],
) -> float:
    """
    Catalog Coverage = |union(recommended_ids across all users)| / |unique catalog_ids|
    """
    cat_set = set(catalog_ids)
    if not cat_set:
        return 0.0
    rec_union: Set[str] = set()
    for recs in all_recommended_ids:
        rec_union.update(recs)
    return len(rec_union.intersection(cat_set)) / float(len(cat_set))


def intra_list_diversity(item_tags_list: Sequence[str]) -> float:
    """
    Intra-list Diversity (ILD) using pairwise Jaccard distance over tag tokens:
      ILD = (2 / (N * (N - 1))) * sum_{i < j} (1 - |T_i & T_j| / |T_i | T_j|)
    Returns 0.0 if fewer than 2 items.
    """
    n = len(item_tags_list)
    if n < 2:
        return 0.0

    token_sets = [set(str(t).lower().split()) for t in item_tags_list]
    total_dist = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            union = token_sets[i].union(token_sets[j])
            if not union:
                dist = 0.0
            else:
                inter = token_sets[i].intersection(token_sets[j])
                dist = 1.0 - (len(inter) / float(len(union)))
            total_dist += dist
            pairs += 1
    return total_dist / float(pairs) if pairs > 0 else 0.0


def is_dietary_violation(tags: str, dietary_exclusions: Optional[Sequence[str]]) -> bool:
    """
    Check if a single item's tags violate any requested dietary exclusion.
    - 'chay'/'vegetarian'/'vegan': must contain explicit vegetarian token AND must not contain meat tokens.
    - 'không cay': must not contain spicy tokens ('cay', 'sa tế', 'mì cay', 'ớt').
    - 'halal': must contain 'halal' or 'muslim'.
    """
    if not dietary_exclusions:
        return False
    tags_lower = str(tags or "").lower()
    for ex in dietary_exclusions:
        ex_clean = str(ex).strip().lower()
        if any(tok in ex_clean for tok in ("chay", "vegetarian", "vegan")):
            has_veg = any(tok in tags_lower for tok in ("chay", "vegan", "vegetarian"))
            has_meat = any(tok in tags_lower for tok in ("thịt", "gà", "bò", "heo", "cá", "tôm", "mực", "hải sản", "ốc"))
            if not has_veg or has_meat:
                return True
        elif "không cay" in ex_clean:
            if any(tok in tags_lower for tok in ("cay", "sa tế", "mì cay", "ớt")):
                return True
        elif "halal" in ex_clean:
            if not any(tok in tags_lower for tok in ("halal", "muslim")):
                return True
    return False


def dietary_constraint_violation_rate(
    recommended_items: Sequence[Dict[str, str]],
    dietary_exclusions: Optional[Sequence[str]],
) -> float:
    """
    Fraction of recommended items that violate dietary_exclusions.
    Returns 0.0 when recommended_items is empty or no exclusions are set.
    """
    if not recommended_items or not dietary_exclusions:
        return 0.0
    violations = sum(
        1 for item in recommended_items
        if is_dietary_violation(item.get("tags", ""), dietary_exclusions)
    )
    return violations / float(len(recommended_items))


def compute_summary_stats(values: Sequence[float]) -> Dict[str, float]:
    """
    Compute sample size, mean, sample variance, sample std, min, max, and 95% CI.
    Uses normal-approximation 1.96 * SE for n > 1 (documented as descriptive for small N).
    """
    n = len(values)
    if n == 0:
        return {
            "n": 0,
            "mean": 0.0,
            "std": 0.0,
            "variance": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_95_low": 0.0,
            "ci_95_high": 0.0,
        }
    mean_val = sum(values) / float(n)
    if n > 1:
        var_val = sum((x - mean_val) ** 2 for x in values) / float(n - 1)
        std_val = math.sqrt(var_val)
        se = std_val / math.sqrt(n)
        margin = 1.96 * se
    else:
        var_val = 0.0
        std_val = 0.0
        margin = 0.0
    return {
        "n": n,
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "variance": round(var_val, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "ci_95_low": round(max(0.0, mean_val - margin), 4),
        "ci_95_high": round(min(1.0, mean_val + margin), 4),
    }
