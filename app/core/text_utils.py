import math
from app.config import LOCATION_NAMES, EN_VI_MAPPING

def clean_coordinate(val):
    try:
        if isinstance(val, (int, float)): 
            return float(val)
        if isinstance(val, str): 
            return float(val.replace(',', '.'))
        return 0.0
    except Exception:
        return 0.0

def clean_price(val):
    try:
        s = str(val)
        clean_s = ''.join(filter(str.isdigit, s))
        if clean_s:
            return float(clean_s)
        return 0.0
    except Exception:
        return 0.0

def extract_district_from_address(address: str) -> str:
    if not isinstance(address, str): 
        return ''
    addr_lower = address.lower()
    
    # Sort keys by length in descending order to match longer keywords first (e.g. 'Quận 12' before 'Quận 1')
    sorted_locations = sorted(LOCATION_NAMES.keys(), key=len, reverse=True)
    
    for k in sorted_locations:
        if k in addr_lower:
            return LOCATION_NAMES[k]
            
    return ''

def translate_query(query: str) -> str:
    query_lower = query.lower()
    for k, v in EN_VI_MAPPING.items():
        if f" {k} " in f" {query_lower} ":
            query_lower = query_lower.replace(k, v)
    return query_lower

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if any(x is None for x in [lat1, lon1, lat2, lon2]): 
        return 999.0
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        R = 6371.0 
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return 999.0
