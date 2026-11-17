# GASTROWISE - AI EVALUATION, METRICS & CONTINUOUS MONITORING
## Quantitative Benchmarks, Evaluation Protocols, and MLOps Drift Detection Pipeline

**Module:** `KLTN-123-GastroWise-AI / app/evaluation/`  
**Applicability:** Recommendation Engine, Route Optimization, Computer Vision, MLOps Telemetry  
**Status:** Architecture Specification & Evaluation Standards  

---

## 1. High-Level AI Quality Framework

GastroWise evaluates AI systems across three rigorous dimensions:
1. **Offline Model Benchmarking:** Evaluates algorithmic precision, recall, ranking quality, and constraint satisfaction against held-out ground truth datasets prior to production deployment.
2. **Online Telemetry & Business Impact:** Measures real-world user engagement, conversion funnel, itinerary completion rates, and Taste DNA convergence.
3. **Continuous Drift & MLOps Monitoring:** Detects feature distribution shifts, concept drift, and degradation of model accuracy, automatically triggering retraining pipelines.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   GastroWise AI Quality Lifecycle                      │
├──────────────────┬──────────────────────┬──────────────────────────────┤
│ Offline Metrics  │ Online Telemetry     │ Continuous Monitoring        │
│ • NDCG@K, MRR    │ • Recommendation CTR │ • Population Stability (PSI) │
│ • Tour Distance  │ • Tour Completion    │ • KS-Test Feature Drift      │
│ • mAP@50 / 95    │ • Taste DNA Stability│ • Automated Retrain Triggers │
└──────────────────┴──────────────────────┴──────────────────────────────┘
```

---

## 2. Recommendation Engine Evaluation Metrics

The Hybrid Recommendation Engine (`app/core/recommender.py`) is evaluated against historical user interaction logs (`user_interactions`), partitioning data into 80% train, 10% validation, and 10% held-out test sets using time-based splitting to prevent future data leakage.

### 2.1. Ranking & Retrieval Metrics

#### A. Normalized Discounted Cumulative Gain (NDCG@K)
Measures the ranking quality by giving higher credit to relevant restaurant recommendations placed near the top of the list.

$$\text{DCG}@K = \sum_{i=1}^K \frac{2^{rel_i} - 1}{\log_2(i + 1)}$$

$$\text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$

Where:
- $rel_i \in \{0, 1, 2, 3, 4\}$ denotes interaction relevance:
  - $0$: Ignored / Scrolled past
  - $1$: Clicked / Viewed details
  - $2$: Added to itinerary or saved to favorites
  - $3$: Visited / Marked complete
  - $4$: 5-star review left
- $\text{IDCG}@K$: Ideal DCG obtained by sorting items strictly in descending order of relevance.

#### B. Precision@K and Recall@K
Evaluates binary relevance (relevance score $rel_i \ge 2$):

$$\text{Precision}@K = \frac{|\text{Relevant Items} \cap \text{Top-}K|}{K}$$

$$\text{Recall}@K = \frac{|\text{Relevant Items} \cap \text{Top-}K|}{|\text{All Relevant Items for User } u|}$$

#### C. Mean Reciprocal Rank (MRR)
Measures how quickly the user encounters their first truly relevant restaurant:

$$\text{MRR} = \frac{1}{|U|} \sum_{u=1}^{|U|} \frac{1}{\text{rank}_u^*}$$

Where $\text{rank}_u^*$ is the 1-based rank position of the first clicked or saved restaurant.

### 2.2. Diversity, Coverage & Novelty Metrics

#### A. Intra-List Diversity (ILD)
Ensures recommendation lists do not over-concentrate on a single cuisine or flavor profile:

$$\text{ILD}(L) = \frac{2}{|L|(|L|-1)} \sum_{i \in L} \sum_{j \in L, j > i} \left(1 - \text{CosineSim}(\vec{V}_i, \vec{V}_j)\right)$$

Where $\vec{V}_i, \vec{V}_j$ are the 6-D Taste DNA flavor vectors of restaurants $i$ and $j$.

#### B. Catalog Coverage
Measures the proportion of available restaurants in the database exposed to at least one user over time:

$$\text{Catalog Coverage} = \frac{|\bigcup_{u \in U} \text{Top-}K(u)|}{|\mathcal{I}_{\text{total}}|}$$

#### C. Gini Coefficient of Exposure
Measures inequality in restaurant exposure to detect "superstar bias":

$$G = \frac{\sum_{i=1}^N \sum_{j=1}^N |e_i - e_j|}{2 N \sum_{i=1}^N e_i}$$

Where $e_i$ is the number of times restaurant $i$ was recommended. A lower $G$ ($< 0.45$) guarantees fair exposure for local street food vendors.

### 2.3. Recommendation Target Benchmarks

| Metric | Baseline (Random / Popularity) | Phase 1 (TF-IDF Content Only) | Phase 2 Target (Hybrid SVD + Taste DNA) | SLA / Minimum Pass |
| :--- | :--- | :--- | :--- | :--- |
| **NDCG@5** | 0.382 | 0.584 | **$\ge 0.760$** | 0.720 |
| **NDCG@10** | 0.415 | 0.612 | **$\ge 0.795$** | 0.750 |
| **Precision@5** | 0.120 | 0.280 | **$\ge 0.440$** | 0.380 |
| **Recall@10** | 0.190 | 0.390 | **$\ge 0.620$** | 0.550 |
| **MRR** | 0.245 | 0.490 | **$\ge 0.680$** | 0.600 |
| **Catalog Coverage** | 18.5% | 42.0% | **$\ge 68.0\%$** | 55.0% |
| **Intra-List Diversity**| 0.120 | 0.310 | **$\ge 0.480$** | 0.400 |

---

## 3. Route Optimization Evaluation Metrics

The TSPTW Route Optimizer (`app/core/route_optimizer.py`) is benchmarked against exact mathematical baselines and greedy heuristic approaches.

### 3.1. Algorithmic Optimization Metrics

#### A. Tour Distance Reduction vs Heuristic Baseline
Measures the percentage improvement in total road transit distance compared to a greedy nearest-neighbor route:

$$\Delta D = \frac{D_{\text{Greedy}} - D_{\text{OR-Tools}}}{D_{\text{Greedy}}} \times 100\%$$

- **Target:** $\Delta D \ge 22.0\%$ distance reduction across 3-to-6 stop tours.

#### B. Time Window Violation Rate
Measures whether any recommended stop schedules an arrival outside operational restaurant hours:

$$\text{TWVR} = \frac{\sum_{i=1}^n \mathbb{I}(t_i < e_i \lor t_i > l_i)}{n} \times 100\%$$

- **Target:** **Strictly 0.0%**. A non-zero rate is considered a critical solver failure.

#### C. Gastronomic Order Compliance Rate
Measures whether culinary progression constraints (e.g. Appetizer $\to$ Main Course $\to$ Dessert / Cafe) are respected:

$$\text{GOCR} = \frac{\text{Conforming Transitions}}{\text{Total Transitions}} \times 100\%$$

- **Target:** **100.0%** compliance.

#### D. Solver Latency Benchmark
Optimization runs on demand when the user requests an itinerary or adjusts stops.

| Stops Count | 50th Percentile (p50) | 95th Percentile (p95) | 99th Percentile (p99) | Timeout Hard Limit |
| :--- | :--- | :--- | :--- | :--- |
| **3 Stops** | 22 ms | 48 ms | 85 ms | 500 ms |
| **5 Stops** | 55 ms | 120 ms | 195 ms | 1,000 ms |
| **8 Stops** | 140 ms | 290 ms | 480 ms | 2,500 ms |

---

## 4. Computer Vision (Food Recognition) Evaluation Metrics

The YOLOv11m Vietnamese Food Vision model (`app/core/vision_service.py`) is evaluated on a test set of 2,000 annotated images across all 20 target Vietnamese dish classes.

### 4.1. Detection & Classification Metrics

#### A. Mean Average Precision at IoU 0.50 (mAP@50)
Evaluates precision across all recall values with an Intersection-over-Union threshold of $0.50$:

$$\text{AP}_c = \int_0^1 p_c(r) \, dr \quad \implies \quad \text{mAP}@50 = \frac{1}{C} \sum_{c=1}^{C} \text{AP}_c^{50}$$

- **Target:** $\text{mAP}@50 \ge 86.5\%$ across all 20 classes.

#### B. Mean Average Precision at IoU 0.50:0.95 (mAP@50:95)
Measures bounding box localization quality across IoU thresholds from 0.50 to 0.95 with step 0.05:

- **Target:** $\text{mAP}@50:95 \ge 64.0\%$.

### 4.2. Per-Class Benchmark Targets (20 Dishes)

| Class Name | Target mAP@50 | Precision@0.5 | Recall@0.5 | High-Risk Confusion Classes |
| :--- | :--- | :--- | :--- | :--- |
| **Banh-Mi** | 94.5% | 0.93 | 0.91 | Gỏi Cuốn (wrapper similarity) |
| **Banh-Xeo** | 91.0% | 0.90 | 0.88 | Bột Chiên (fried egg texture) |
| **Banh-Cuon** | 88.5% | 0.87 | 0.86 | Phở Cuốn, Hủ Tiếu ướt |
| **Bot-Chien** | 89.0% | 0.88 | 0.85 | Bánh Xèo vụn |
| **Bun-Bo-Hue** | 87.5% | 0.86 | 0.85 | Bún Riêu (red broth reflection) |
| **Bun-Cha** | 90.0% | 0.89 | 0.88 | Nem Nướng |
| **Bun-Dau-Mam-Tom**| 93.0% | 0.92 | 0.91 | Gỏi Cuốn (tofu/herb platter) |
| **Bun-Rieu** | 85.5% | 0.84 | 0.83 | Bún Bò Huế |
| **Com-Tam** | 92.5% | 0.91 | 0.90 | Cơm Gà |
| **Com-Ga** | 89.5% | 0.88 | 0.87 | Cơm Tấm |
| **Goi-Cuon** | 91.5% | 0.90 | 0.89 | Chả Giò |
| **Hu-Tieu** | 84.0% | 0.82 | 0.81 | Phở, Mì Quảng |
| **Mi-Quang** | 86.0% | 0.85 | 0.83 | Cao Lầu (noodle similarity) |
| **Cao-Lau** | 83.5% | 0.81 | 0.80 | Mì Quảng |
| **Nem-Nuong** | 88.0% | 0.86 | 0.85 | Bún Chả chả viên |
| **Oc-Xao-Me** | 85.0% | 0.83 | 0.82 | Hột Vịt Lộn xào me |
| **Lau-Thai** | 86.5% | 0.85 | 0.84 | Canh Chua cá |
| **Ca-Phe-Sua-Da** | 95.0% | 0.94 | 0.93 | Trà Sữa |
| **Ca-Phe-Trung** | 91.0% | 0.90 | 0.89 | Flan / Pudding |
| **Che-Thai** | 87.0% | 0.85 | 0.84 | Trái Cây Dầm |

### 4.3. Out-of-Distribution (OOD) & False Positive Rejection
- **Test Condition:** 500 non-Vietnamese food images (Pizza, Sushi, Burgers) and 500 non-food images (Laptops, cats, cars).
- **Target Metric:** $\text{False Positive Rate} \le 5.0\%$ when confidence threshold $\theta = 0.45$.
- Images falling below $\theta = 0.45$ are safely rejected with `is_confident: false` and mapped to general category exploration.

---

## 5. Online Telemetry & Business Impact Metrics

Offline metrics validate algorithmic health, but online metrics measure actual business value.

### 5.1. Product Interaction Metrics

```
[Recommendation Impression]
            │
            ▼  Target CTR >= 18.0%
    [Item Card Click]
            │
            ▼  Target Conversion >= 28.0%
   [Added to Itinerary]
            │
            ▼  Target Completion >= 65.0%
[Itinerary Completed / Visited]
            │
            ▼  Target Feedback Rate >= 15.0%
     [5-Star Review]
```

1. **Click-Through Rate (CTR):**
   $$\text{CTR} = \frac{\text{Unique Clicks on Recommended Items}}{\text{Total Recommendation Impressions}} \times 100\% \quad (\text{Target: } \ge 18.0\%)$$

2. **Itinerary Completion Rate (ICR):**
   $$\text{ICR} = \frac{\text{Itineraries Marked COMPLETED}}{\text{Total Created Itineraries}} \times 100\% \quad (\text{Target: } \ge 65.0\%)$$

3. **Taste DNA Stability Metric:**
   Measures exponential convergence of a user's 6-D vector over consecutive interactions:
   $$\delta_w = \|\vec{V}_{u}^{(w+1)} - \vec{V}_{u}^{(w)}\|_2$$
   - A healthy profile exhibits $\delta_w < 0.05$ after $\ge 12$ recorded dining interactions.

---

## 6. Continuous Monitoring & MLOps Drift Detection

Production data evolves as seasons, food trends, and user preferences shift. GastroWise implements automated drift detection via weekly automated cron jobs in `KLTN-123-GastroWise-AI`.

### 6.1. Population Stability Index (PSI) for Feature Drift

Monitors changes in the distributions of the 6-D Taste DNA scores and restaurant distance distributions between reference baseline $B$ and production inference batches $P$:

$$\text{PSI} = \sum_{b=1}^B \left( P_b - B_b \right) \times \ln\left(\frac{P_b}{B_b}\right)$$

| PSI Value Range | Action Required | Status |
| :--- | :--- | :--- |
| **$\text{PSI} < 0.10$** | No significant shift; distribution stable. |  Healthy |
| **$0.10 \le \text{PSI} < 0.25$** | Moderate shift detected; log warning in Prometheus. | ⚠️ Warning |
| **$\text{PSI} \ge 0.25$** | Significant feature drift; trigger automated model retraining. | 🚨 Retrain Required |

### 6.2. Kolmogorov-Smirnov (KS) Test for Numerical Outputs
A two-sample Kolmogorov-Smirnov test is computed daily comparing the predicted composite scores $S_{\text{final}}$ of the current 24-hour window against the 30-day trailing baseline:

- If $p\text{-value} < 0.01$, an alert is dispatched to Sentry and the system falls back to balanced content-based ranking weights ($w_1 = 0.70, w_2 = 0.0, w_3 = 0.30$).

### 6.3. Automated Retraining Pipelines

```
[Production Telemetry Logged]
              │
              ▼
    [Weekly PSI / KS Check]
              │
       ┌──────┴──────┐
 PSI >= 0.25    PSI < 0.25
       │             │
       ▼             ▼
[Trigger Retrain] [Keep Current Model]
       │
       ▼
1. Recompute SVD Latent Vectors (user_interactions)
2. Recalibrate Restaurant Taste DNA Centroids
3. Run Regression Benchmark Suite (NDCG@10 >= 0.75)
       │
       ▼  Passes Benchmark?
   ┌───┴───┐
  YES      NO
   │        │
   ▼        ▼
[Hot-Reload] [Page On-Call & Abort Deployment]
```

1. **Latent Matrix Factorization Retraining:**
   - **Frequency:** Every Sunday at 02:00 UTC.
   - **Trigger:** Automated cron in backend invoking `POST /ai/recommender/retrain` with internal API key.
   - **Validation Gate:** New model artifact (`svd_model.pkl`) is only hot-reloaded into memory if validation NDCG@10 does not regress by more than $2.0\%$ compared to production.

2. **Food Vision Model Retraining:**
   - **Trigger:** When $\ge 500$ verified user review photos are accumulated in `ai_food_feedback` with confirmed labels.
   - **Pipeline:** Runs 30 fine-tuning epochs on NVIDIA T4 GPU; accepted only if overall $\text{mAP}@50 \ge 86.5\%$.

---

## 7. A/B Testing Experimentation Framework

To evaluate new algorithmic enhancements without risking user experience, GastroWise employs deterministic user hashing:

```python
import mmh3

def assign_experiment_bucket(user_id: str, experiment_name: str) -> str:
    """
    Deterministically assigns a user to Control (A) or Treatment (B)
    using MurmurHash3 to avoid sticky cross-experiment bias.
    """
    seed_str = f"{user_id}:{experiment_name}"
    bucket = mmh3.hash(seed_str) % 100
    
    if bucket < 50:
        return "CONTROL_A"       # 50% Baseline (Content-Based Recommender)
    else:
        return "TREATMENT_B"     # 50% Hybrid AI (SVD + Weather + OR-Tools)
```

The gateway appends `X-Experiment-Group: CONTROL_A | TREATMENT_B` to all response headers and event tracking pipelines, enabling direct statistical significance testing (Student's t-test with $p < 0.05$) on CTR and tour completions in the Admin Analytics Dashboard.

