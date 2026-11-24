import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sklearn.decomposition import TruncatedSVD
from app.core.rating_normalizer import normalize_rating

EVENT_WEIGHTS = {
    'VIEW': 1.0,
    'CLICK': 1.5,
    'SEARCH': 1.0,
    'SAVE': 3.0,
    'FAVORITE': 3.0,
    'REVIEW': 4.0,
    'TOUR_COMPLETE': 5.0,
    'ITINERARY_COMPLETE': 5.0,
}

class CollaborativeFilteringEngine:
    """
    [TASK-P2-02] Collaborative Filtering Engine sử dụng TruncatedSVD Matrix Factorization.
    Mô hình hóa ma trận tương tác người dùng - nhà hàng:
    R_hat(u, r) = mu + b_u + b_r + p_u^T * q_r
    """
    def __init__(self, n_factors: int = 10):
        self.n_factors = n_factors
        self.is_trained = False
        self.user_to_idx: Dict[str, int] = {}
        self.item_to_idx: Dict[str, int] = {}
        self.idx_to_user: Dict[int, str] = {}
        self.idx_to_item: Dict[int, str] = {}
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        self.global_mean: float = 0.0
        self.user_bias: Optional[np.ndarray] = None
        self.item_bias: Optional[np.ndarray] = None
        self.user_interaction_counts: Dict[str, int] = {}

    def is_user_cold_start(self, user_id: str) -> bool:
        """Kiểm tra xem người dùng có phải cold-start không (< 2 tương tác)."""
        if not user_id or user_id not in self.user_to_idx:
            return True
        return self.user_interaction_counts.get(user_id, 0) < 2

    def train_from_interactions(self, interactions: List[Dict]) -> bool:
        """
        Huấn luyện SVD từ danh sách interaction records.
        Mỗi interaction: { userId: str, targetId: str, eventType: str, rating?: float }
        """
        if not interactions or len(interactions) < 2:
            print("[CF Engine] Dữ liệu tương tác chưa đủ để huấn luyện SVD (< 2 records).")
            self.is_trained = False
            return False

        try:
            records = []
            user_counts: Dict[str, int] = {}

            for item in interactions:
                u_id = str(item.get('userId') or item.get('user_id') or '').strip()
                t_id = str(item.get('targetId') or item.get('target_id') or item.get('restaurantId') or '').strip()
                e_type = str(item.get('eventType') or item.get('event_type') or 'VIEW').upper()

                if not u_id or not t_id:
                    continue

                weight = EVENT_WEIGHTS.get(e_type, 1.0)
                # Nếu có rating riêng từ review (chuẩn hóa về thang 5)
                if 'rating' in item and item['rating'] is not None:
                    try:
                        r_val = normalize_rating(item['rating'], default=0.0)
                        if r_val > 0.0:
                            weight = max(weight, r_val)
                    except (ValueError, TypeError):
                        pass

                records.append({'user': u_id, 'item': t_id, 'weight': weight})
                user_counts[u_id] = user_counts.get(u_id, 0) + 1

            if not records:
                return False

            df_inter = pd.DataFrame(records)
            # Gom nhóm tổng điểm tương tác giữa user và item
            grouped = df_inter.groupby(['user', 'item'])['weight'].sum().reset_index()

            users = grouped['user'].unique().tolist()
            items = grouped['item'].unique().tolist()

            n_users = len(users)
            n_items = len(items)

            self.user_to_idx = {u: i for i, u in enumerate(users)}
            self.item_to_idx = {it: i for i, it in enumerate(items)}
            self.idx_to_user = {i: u for i, u in enumerate(users)}
            self.idx_to_item = {i: it for i, it in enumerate(items)}
            self.user_interaction_counts = user_counts

            # Xây dựng ma trận tương tác
            R = np.zeros((n_users, n_items), dtype=np.float32)
            for _, row in grouped.iterrows():
                u_idx = self.user_to_idx[row['user']]
                i_idx = self.item_to_idx[row['item']]
                R[u_idx, i_idx] = float(row['weight'])

            # Tính biases
            self.global_mean = float(np.mean(R[R > 0])) if np.any(R > 0) else 1.0
            
            # User & Item biases
            self.user_bias = np.zeros(n_users, dtype=np.float32)
            for u_idx in range(n_users):
                u_ratings = R[u_idx, R[u_idx, :] > 0]
                if len(u_ratings) > 0:
                    self.user_bias[u_idx] = np.mean(u_ratings) - self.global_mean

            self.item_bias = np.zeros(n_items, dtype=np.float32)
            for i_idx in range(n_items):
                i_ratings = R[R[:, i_idx] > 0, i_idx]
                if len(i_ratings) > 0:
                    self.item_bias[i_idx] = np.mean(i_ratings) - self.global_mean

            # Chuẩn hóa ma trận trừ mean và bias
            R_centered = np.copy(R)
            for u_idx in range(n_users):
                for i_idx in range(n_items):
                    if R[u_idx, i_idx] > 0:
                        R_centered[u_idx, i_idx] -= (self.global_mean + self.user_bias[u_idx] + self.item_bias[i_idx])

            # Huấn luyện TruncatedSVD
            effective_factors = min(self.n_factors, max(1, min(n_users, n_items) - 1))
            if effective_factors >= 1 and min(n_users, n_items) >= 2:
                svd = TruncatedSVD(n_components=effective_factors, random_state=42)
                self.user_factors = svd.fit_transform(R_centered)
                self.item_factors = svd.components_.T
            else:
                self.user_factors = np.zeros((n_users, 1), dtype=np.float32)
                self.item_factors = np.zeros((n_items, 1), dtype=np.float32)

            self.is_trained = True
            print(f"[CF Engine] Huấn luyện thành công SVD với {n_users} users, {n_items} items, {effective_factors} latent factors.")
            return True

        except Exception as e:
            print(f"[CF Engine] Lỗi huấn luyện SVD: {e}")
            self.is_trained = False
            return False

    def predict_score(self, user_id: str, restaurant_id: str) -> float:
        """
        Dự đoán điểm sở thích của user u với restaurant r trong [0.0, 1.0].
        Nếu user hoặc item chưa có trong mô hình, trả về 0.0 (Cold-start).
        """
        if not self.is_trained:
            return 0.0

        if not user_id or user_id not in self.user_to_idx:
            return 0.0

        if not restaurant_id or restaurant_id not in self.item_to_idx:
            return 0.0

        u_idx = self.user_to_idx[user_id]
        i_idx = self.item_to_idx[restaurant_id]

        u_vec = self.user_factors[u_idx]
        i_vec = self.item_factors[i_idx]

        latent_dot = float(np.dot(u_vec, i_vec))
        u_b = float(self.user_bias[u_idx]) if self.user_bias is not None else 0.0
        i_b = float(self.item_bias[i_idx]) if self.item_bias is not None else 0.0

        raw_pred = self.global_mean + u_b + i_b + latent_dot

        # Chuẩn hóa về [0.0, 1.0] bằng hàm sigmoid biến thể
        normalized_score = 1.0 / (1.0 + np.exp(-0.5 * (raw_pred - 2.5)))
        return float(np.clip(normalized_score, 0.0, 1.0))

# Global Singleton Instance
cf_engine = CollaborativeFilteringEngine()

