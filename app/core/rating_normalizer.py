import math
from typing import Any, Dict, Optional, Tuple, Union
from enum import Enum

class RatingScale(str, Enum):
    SCALE_10 = "10_point"
    SCALE_5 = "5_point"
    AUTO = "auto"

DEFAULT_NEUTRAL_RATING = 3.0
MIN_RATING = 0.0
MAX_RATING = 5.0
MAX_RAW_10 = 10.0

def _resolve_scale(scale: Union[RatingScale, str]) -> RatingScale:
    if isinstance(scale, RatingScale):
        return scale
    s = str(scale).strip().lower()
    if s in (RatingScale.SCALE_10.value, "10", "10_point", "scale_10", "ratingscale.scale_10"):
        return RatingScale.SCALE_10
    if s in (RatingScale.SCALE_5.value, "5", "5_point", "scale_5", "ratingscale.scale_5"):
        return RatingScale.SCALE_5
    return RatingScale.AUTO

def normalize_rating(
    val: Any,
    scale: Union[RatingScale, str] = RatingScale.AUTO,
    default: float = DEFAULT_NEUTRAL_RATING,
    is_already_normalized: bool = False
) -> float:
    """
    Chuẩn hóa giá trị đánh giá về thang 5 sao [0.0, 5.0] an toàn, nhất quán.
    
    Quy tắc:
    - Nếu is_already_normalized=True: Giữ nguyên (tránh double normalization), clamp [0.0, 5.0].
    - Nếu val là None, NaN, rỗng, không phải số: Trả về default (mặc định 3.0).
    - Nếu val < 0.0: Clamp về 0.0.
    - Nếu val > 10.0: Clamp về 5.0 (tương đương 10/10).
    - Nếu scale == SCALE_10: r / 2.0.
    - Nếu scale == SCALE_5: giữ nguyên trong [0.0, 5.0].
    - Nếu scale == AUTO:
        + Nếu r > 5.0: chắc chắn thang 10 -> r / 2.0.
        + Nếu r <= 5.0: coi là đã ở thang 5 -> giữ nguyên.
    """
    if is_already_normalized:
        try:
            r = float(val)
            if math.isnan(r) or math.isinf(r):
                return default
            return round(max(MIN_RATING, min(MAX_RATING, r)), 1)
        except (ValueError, TypeError):
            return default

    if val is None:
        return default

    # Kiểm tra float/nan
    try:
        r = float(val)
    except (ValueError, TypeError):
        return default

    if math.isnan(r) or math.isinf(r):
        return default

    # Xử lý giá trị âm
    if r < MIN_RATING:
        return MIN_RATING

    # Xử lý giá trị vượt quá thang 10 tối đa
    if r > MAX_RAW_10:
        return MAX_RATING

    resolved_scale = _resolve_scale(scale)
    if resolved_scale == RatingScale.SCALE_10:
        normalized = r / 2.0
    elif resolved_scale == RatingScale.SCALE_5:
        normalized = r
    else:  # AUTO
        if r > 5.0:
            normalized = r / 2.0
        else:
            normalized = r

    # Clamp kết quả cuối cùng về [0.0, 5.0] và làm tròn 1 chữ số thập phân
    normalized = max(MIN_RATING, min(MAX_RATING, normalized))
    return round(normalized, 1)

def detect_restaurant_rating_scale(doc: Dict[str, Any]) -> Tuple[RatingScale, float]:
    """
    Tự động phát hiện thang điểm của bản ghi nhà hàng dựa trên siêu dữ liệu:
    - Nếu có reviewsCount > 0 và không có điểm thành phần crawler: Thang 5 (do người dùng GastroWise review).
    - Nếu có điểm thành phần Foody (diemChatLuong, diemViTri, diemPhucVu, urlGoc): Thang 10 ban đầu.
    - Nếu diemTrungBinh > 5.0: Chắc chắn thang 10.
    - Trả về (detected_scale, raw_rating).
    """
    raw_val = doc.get('diemTrungBinh')
    if raw_val is None:
        raw_val = doc.get('rating')

    try:
        raw_num = float(raw_val) if raw_val is not None else None
    except (ValueError, TypeError):
        raw_num = None

    if raw_num is None or math.isnan(raw_num) or math.isinf(raw_num):
        return RatingScale.AUTO, DEFAULT_NEUTRAL_RATING

    # Nếu đã đánh dấu đã chuẩn hóa
    if doc.get('_rating_normalized') is True or doc.get('raw_rating') is not None:
        return RatingScale.SCALE_5, raw_num

    # Nếu > 5.0 chắc chắn là thang 10
    if raw_num > 5.0:
        return RatingScale.SCALE_10, raw_num

    # Kiểm tra xem có phải dữ liệu Foody crawler không (có điểm thành phần)
    has_foody_subscores = any(
        doc.get(k) is not None for k in ('diemChatLuong', 'diemViTri', 'diemPhucVu', 'diemGiaCa', 'diemKhongGian')
    )
    reviews_count = doc.get('reviewsCount', 0) or 0

    if has_foody_subscores and reviews_count == 0:
        # Dữ liệu gốc Foody, điểm <= 5.0 (ví dụ 4.0/10) vẫn là thang 10
        return RatingScale.SCALE_10, raw_num
    elif reviews_count > 0:
        # Được cập nhật bởi review của người dùng GastroWise (thang 5 sao)
        return RatingScale.SCALE_5, raw_num

    # Mặc định an toàn
    return RatingScale.AUTO, raw_num

def normalize_restaurant_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa dict nhà hàng:
    - Lưu lại raw_rating gốc.
    - Tính toán rating chuẩn hóa [0.0, 5.0].
    - Đánh dấu _rating_normalized = True để tránh double normalization.
    """
    if doc.get('_rating_normalized') is True:
        return doc

    scale, raw_num = detect_restaurant_rating_scale(doc)
    doc['raw_rating'] = raw_num
    doc['raw_rating_scale'] = scale.value
    doc['rating'] = normalize_rating(raw_num, scale=scale)
    doc['_rating_normalized'] = True
    return doc
