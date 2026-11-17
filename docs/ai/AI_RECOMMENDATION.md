# GASTROWISE - HYBRID AI RECOMMENDATION ENGINE SPECIFICATION
## Multi-Stage Candidate Generation, Collaborative Filtering & Context-Aware Ranking

**Module:** `KLTN-123-GastroWise-AI / app/core/recommender.py`  
**Frameworks:** Scikit-Learn, NumPy, PyMongo, Pandas, Open-Meteo API  

---

## 1. High-Level Architecture Pipeline

The GastroWise Recommendation Engine implements a multi-stage industrial recommendation funnel:

```
[All 1,000+ Restaurants in Catalog]
             │
             ▼  Stage 1: Candidate Generation (Hard Constraints)
[Top 150 Candidates] - Filtered by 2dsphere GPS radius, operational status (isOpen),
                     and strict dietary exclusions (e.g. Vegetarian, Halal).
             │
             ▼  Stage 2: Hybrid Scoring (Content-Based + SVD Collaborative)
[Top 50 Ranked]     - Evaluates 6-D Taste DNA cosine similarity and Latent Factor model.
             │
             ▼  Stage 3: Context-Aware Weighting & Weather Adaptation
[Top 20 Ordered]    - Ingests real-time temperature/rain and meal time slots.
             │
             ▼  Stage 4: Explainability & Deduplication
[Final 10 Output]   - Attaches human-readable justification pills (e.g. "85% Taste Match").
```

---

## 2. Mathematical Modeling & Scoring Formulas

### 2.1. Content-Based Taste DNA Matching
Each user $u$ possesses a normalized 6-dimensional flavor vector $\vec{V}_u = (v_{\text{spicy}}, v_{\text{sweet}}, v_{\text{sour}}, v_{\text{salty}}, v_{\text{umami}}, v_{\text{bitter}})$. Each restaurant $r$ has a centroid profile $\vec{V}_r$ computed from its menu items and tags.

The base Taste Similarity score is computed via Cosine Similarity:

$$S_{\text{taste}}(u, r) = \frac{\vec{V}_u \cdot \vec{V}_r}{\|\vec{V}_u\|_2 \|\vec{V}_r\|_2} = \frac{\sum_{k=1}^6 V_{u,k} V_{r,k}}{\sqrt{\sum_{k=1}^6 V_{u,k}^2} \sqrt{\sum_{k=1}^6 V_{r,k}^2}}$$

Where $S_{\text{taste}} \in [0.0, 1.0]$.

### 2.2. Collaborative Filtering (Matrix Factorization / SVD)
For users with $\ge 5$ interaction events in `user_interactions`, we compute user latent vector $\mathbf{p}_u \in \mathbb{R}^d$ and restaurant latent vector $\mathbf{q}_r \in \mathbb{R}^d$ (with $d = 20$ latent dimensions):

$$\hat{R}_{\text{CF}}(u, r) = \mu + b_u + b_r + \mathbf{p}_u^T \mathbf{q}_r$$

Where:
- $\mu$: Global interaction mean.
- $b_u$: User interaction bias.
- $b_r$: Restaurant popularity bias.
- $\mathbf{p}_u, \mathbf{q}_r$: Latent factors learned by TruncatedSVD minimizing regularized squared error:

$$\min_{\mathbf{p}, \mathbf{q}, b} \sum_{(u,r) \in \mathcal{K}} \left( R_{u,r} - \hat{R}_{u,r} \right)^2 + \lambda \left( \|\mathbf{p}_u\|_2^2 + \|\mathbf{q}_r\|_2^2 + b_u^2 + b_r^2 \right)$$

### 2.3. Contextual Weather & Environmental Weight
The environmental context score $S_{\text{env}}(r, \mathcal{C})$ considers ambient temperature $T$ (°C) and precipitation code $W$:

$$S_{\text{env}}(r, \mathcal{C}) = \begin{cases}
1.3 & \text{if } W \in \text{RainCodes} \land r.\text{tags} \cap \{\text{LẨU, MÓN NƯỚNG, NƯỚC DÙNG}\} \neq \emptyset \\
1.3 & \text{if } T \ge 31.0^\circ\text{C} \land r.\text{tags} \cap \{\text{CHÈ, TRÀ SỮA, GỎI, THANH MÁT}\} \neq \emptyset \\
1.0 & \text{otherwise}
\end{cases}$$

### 2.4. Final Composite Ranking Function
The final composite score $S_{\text{final}}(u, r)$ integrates all signals penalized by travel distance $D(u, r)$ (in km):

$$S_{\text{final}}(u, r) = w_1 \cdot S_{\text{taste}}(u, r) + w_2 \cdot \tilde{R}_{\text{CF}}(u, r) + w_3 \cdot S_{\text{env}}(r, \mathcal{C}) - \lambda_{\text{dist}} \cdot \ln(1 + D(u, r))$$

**Recommended Production Hyperparameters:**
- $w_1 = 0.45$ (Taste DNA weight)
- $w_2 = 0.30$ (Collaborative Filtering weight; set to $0$ for cold-start users)
- $w_3 = 0.25$ (Weather & time context weight)
- $\lambda_{\text{dist}} = 0.12$ (Distance decay factor)

---

## 3. Cold-Start Handling Strategy

| Scenario | Challenge | Solution |
| :--- | :--- | :--- |
| **New User (Zero Interactions)** | No interaction history exists for collaborative filtering ($S_{\text{CF}}$ undefined). | 1. Prompt 3-step Taste DNA Questionnaire upon first launch.<br>2. Set $w_2 = 0.0$ and reallocate weight to Taste DNA ($w_1 = 0.65$) + Weather ($w_3 = 0.35$).<br>3. Recommend top-rated verified partners in proximity. |
| **New Restaurant (Zero Reviews)** | Item has zero ratings and cannot be recommended via CF. | 1. Extract menu tags and descriptions using TF-IDF feature vector.<br>2. Give a 14-day "New Merchant Boost" (+0.15 score boost).<br>3. Match purely against Taste DNA content-based filter. |

---

## 4. Explainable Recommendation Synthesizer

To build user trust, the engine generates an explainability string for every recommended item:

```python
def generate_explanation(taste_score: float, cf_score: float, weather_boost: bool, dist_km: float) -> str:
    reasons = []
    if taste_score >= 0.80:
        reasons.append("Hợp khẩu vị Taste DNA của bạn (>= 80%)")
    if weather_boost:
        reasons.append("Món lý tưởng cho thời tiết hiện tại")
    if dist_km <= 1.5:
        reasons.append(f"Rất gần vị trí của bạn ({dist_km:.1f}km)")
    if cf_score >= 0.75:
        reasons.append("Được các thực khách cùng sở thích yêu thích")
        
    return " • ".join(reasons[:2]) if reasons else "Gợi ý được đánh giá cao trên GastroWise"
```

---

## 5. Continuous Online Learning & Weight Updates

When a user interacts with a restaurant (e.g. finishes a food tour or gives a 5-star review), their Taste DNA updates online via Exponential Moving Average:

$$\vec{V}_u^{(t+1)} = (1 - \alpha) \vec{V}_u^{(t)} + \alpha \vec{V}_r$$

Where $\alpha = 0.15$ ensures stability while gradually adapting to evolving culinary tastes.

---

## 6. Resource, Infrastructure & Latency Budget

- **Memory Footprint:** SVD model weights and PyMongo dataframe cache: ~180MB RAM.
- **Latency Target:** Stage 1 + Stage 2 + Stage 3 inference < 60ms on single CPU core.
- **Cost:** 100% self-contained local compute. Zero external LLM token fees for recommendations.

