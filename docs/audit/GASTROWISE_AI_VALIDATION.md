# GASTROWISE – AI MICROSERVICES VALIDATION REPORT

**Audit Date:** November 14, 2026  
**Auditor:** Principal AI Engineer & Machine Learning Architect  
**Scope:** Deep-dive Audit of Machine Learning Models, Optimization Algorithms, NLP Pipelines & Heuristics in `KLTN-123-GastroWise-AI`

---

## 1. AI SUBSYSTEM ARCHITECTURE OVERVIEW

The GastroWise AI platform is engineered as a standalone Python FastAPI microservice (`KLTN-123-GastroWise-AI`), hosting four primary computational pipelines:
1. **Computer Vision:** YOLOv11-based Vietnamese food dish recognition.
2. **Personalized Recommendations:** Hybrid TruncatedSVD Collaborative Filtering + 6D Taste DNA Vector Space + Realtime Weather Context.
3. **Smart Food Journey / Itinerary:** Google OR-Tools Combinatorial TSPTW + Gastronomic Meal Window scheduling.
4. **Natural Language Understanding (Copilot & Sentiment):** ViSoBERT review sentiment analysis + intent parsing.

```
                           ┌──────────────────────────────────────────────┐
                           │            FASTAPI ROUTER (:5000)            │
                           └──────┬────────────┬────────────┬─────────────┘
                                  │            │            │
            ┌─────────────────────┘            │            └─────────────────────┐
            ▼                                  ▼                                  ▼
 ┌──────────────────────┐           ┌──────────────────────┐           ┌──────────────────────┐
 │   COMPUTER VISION    │           │    RECOMMENDATION    │           │  ROUTE OPTIMIZATION  │
 │  - YOLOv11 (best.pt) │           │  - 6D Taste DNA Cos  │           │  - Google OR-Tools   │
 │  - CLAHE + 640x640   │           │  - TruncatedSVD CF   │           │    TSPTW Engine      │
 │  - 5 Dish Classes    │           │  - Open-Meteo Weather│           │  - 1.35x Urban Detour│
 └──────────────────────┘           └──────────────────────┘           └──────────────────────┘
```

---

## 2. DETAILED SUBSYSTEM EVALUATION

### 2.1 Computer Vision: Vietnamese Dish Recognition

| Property | Value / Specification |
| :--- | :--- |
| **Model Weights File** | `app/models/weights/best.pt` (40.5 MB) |
| **Model Architecture** | Ultralytics YOLOv11 (Pre-trained on COCO, fine-tuned on Vietnamese dishes) |
| **Number of Classes** | Exactly **5 Classes**: `pho_bo`, `bun_cha`, `com_tam`, `banh_mi`, `goi_cuon` |
| **Image Preprocessing** | CLAHE (Contrast Limited Adaptive Histogram Equalization) in LAB color space, RGB resize to $640 \times 640$ |
| **Post-Processing** | Non-Maximum Suppression (NMS), Out-of-Distribution (OOD) confidence rejection threshold: **0.45** |
| **Evaluation Script** | `tests/test_vision_food.py` (Functional test passing for sample images) |

#### Real AI vs Heuristic Analysis:
- **Verdict: REAL DEEP LEARNING MODEL.**
- **Limitation:** The model is strictly trained on 5 dishes. If an end user photographs another popular Vietnamese food (e.g. *Bún bò Huế*, *Bánh xèo*, *Mì Quảng*), the confidence score falls below 0.45, triggering an Out-of-Distribution rejection or fallback to text search.
- **Architectural Debt:** The weights file (`40.5 MB`) is committed directly into Git repository history. Best practice recommends hosting large model binaries on HuggingFace Hub or AWS S3 / Cloud Storage with checksum validation on startup.

---

### 2.2 Recommendation Engine: Hybrid Taste DNA & Collaborative Filtering

| Property | Value / Specification |
| :--- | :--- |
| **Taste DNA Representation** | 6-Dimensional Normalized Feature Vector: $[v_{\text{spicy}}, v_{\text{sweet}}, v_{\text{sour}}, v_{\text{salty}}, v_{\text{bitter}}, v_{\text{umami}}] \in [0, 1]^6$ |
| **Content Matching** | Cosine Similarity between User Taste Profile and Restaurant Aggregated Flavor Vector: $\text{CosineSim}(u, r) = \frac{u \cdot r}{\|u\| \|r\|}$ |
| **Collaborative Filtering** | Scikit-learn `TruncatedSVD` matrix factorization ($k=10$ latent components) over user-item interaction matrix |
| **Weather Context** | Open-Meteo API integration: maps temperature, rainfall, and humidity into context score modifiers (e.g. hot soup bonus on rainy/cold days) |
| **Hybrid Blend Formula** | $\text{Score} = 0.5 \cdot \text{CosineSim} + 0.3 \cdot \text{SVDScore} + 0.2 \cdot \text{WeatherScore}$ |
| **Cold-Start Handling** | When user interactions $< 3$, the system switches automatically to **Taste DNA Pure Content Matching** ($\alpha = 0.8, \gamma = 0.2, \beta = 0$) |
| **Evaluation Script** | `tests/test_hybrid_recommendation.py` (Verified passes) |

#### Real AI vs Heuristic Analysis:
- **Verdict: HYBRID (Real Machine Learning + Linear Algebra + Domain Heuristics).**
- SVD and Cosine Vector Space are mathematically sound implementations.
- **Critical Runtime Flaw:** The backend gateway route mismatch (calling `/v1/recommendation/recommend/hybrid` instead of `/recommend/hybrid`) causes NestJS to completely bypass this engine in live usage!

---

### 2.3 Route Optimization: Smart Food Journey / Itinerary

| Property | Value / Specification |
| :--- | :--- |
| **Core Algorithm** | Google OR-Tools TSPTW (Traveling Salesperson Problem with Time Windows) |
| **Meal Slot Heuristics** | - Breakfast: `07:00 – 09:00`<br>- Lunch: `11:30 – 13:30`<br>- Afternoon Coffee/Snack: `15:00 – 17:00`<br>- Dinner: `18:30 – 20:30` |
| **Distance Matrix** | Haversine Great-Circle calculation multiplied by a **1.35x urban detour factor** to approximate real street driving distance |
| **Dependency Flaw** | **`ortools` is MISSING from `requirements.txt`!** Running `pip install -r requirements.txt` on a clean environment will fail on `import ortools`. |
| **Fallback Mechanism** | If the OR-Tools solver times out or fails to converge, the service falls back to a **Greedy Nearest Neighbor** heuristic algorithm |
| **Evaluation Script** | `tests/test_route_optimizer.py` (Passes when `ortools` is manually installed) |

#### Real AI vs Heuristic Analysis:
- **Verdict: OPERATIONAL RESEARCH ALGORITHM (OR-Tools) + HEURISTIC SCHEDULING.**
- Solving TSPTW guarantees mathematically optimal route ordering within meal window constraints.

---

### 2.4 NLP Copilot & Sentiment Analysis

| Property | Value / Specification |
| :--- | :--- |
| **Sentiment Analysis** | ViSoBERT (`vinai/phobert-base` or sentiment classification pipeline) mapping Vietnamese review text to sentiment scores $[-1.0, 1.0]$ |
| **Copilot NLU** | Hybrid Transformer embedding similarity + Regex intent classifier |
| **Supported Intents** | `find_restaurant`, `recommend_dish`, `plan_trip`, `general_inquiry` |
| **Entity Extraction** | Budget/price thresholds, cuisine types, locations/districts, dietary restrictions |
| **Conversational Memory** | Transient in-memory multi-turn session (3 context turns) |
| **Evaluation Script** | `tests/test_nlu_copilot.py` (Verified passes) |

#### Real AI vs Heuristic Analysis:
- **Verdict: HYBRID (Pre-trained Vietnamese Transformer + Pattern Matching).**
- **Critical Runtime Flaw:** Route mismatch in NestJS (`/v1/copilot/message` vs `/copilot/message`) causes Copilot requests to fail with 404, falling back to static keyword regexes in NestJS.

---

## 3. GROUND-TRUTH CLASSIFICATION TABLE

| Component | Implemented Method | Classification | Runtime State in Production |
| :--- | :--- | :--- | :--- |
| **Food Recognition** | YOLOv11n/s (`best.pt`) | **True Deep Learning** | Operates on 5 classes; vulnerable to unvalidated uploads |
| **Taste Profile Match**| 6D Cosine Similarity | **Linear Algebra / Vector Space** | **BYPASSED** due to Gateway 404 URL mismatch |
| **Collaborative Filter**| Scikit-learn `TruncatedSVD` | **True Machine Learning** | **BYPASSED** due to Gateway 404 URL mismatch |
| **Weather Context** | Open-Meteo + Bonus Rules | **Expert System / Heuristic** | **BYPASSED** due to Gateway 404 URL mismatch |
| **Itinerary Optimizer**| Google OR-Tools TSPTW | **Operational Research Algorithm**| Functional (risk: `ortools` missing in `requirements.txt`) |
| **Meal Scheduling** | Fixed Time Windows | **Domain Heuristic** | Functional |
| **Urban Detour Metric**| Haversine $\times$ 1.35 | **Mathematical Approximation**| Functional |
| **Review Sentiment** | ViSoBERT / PhoBERT | **True NLP Transformer** | Functional |
| **Copilot Chatbot** | Hybrid Transformer + Regex | **Hybrid NLU** | **BYPASSED** due to Gateway 404 URL mismatch |

---
*Report certified by Principal AI Engineer & ML Architect.*

