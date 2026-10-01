import requests
from app.config import WEATHER_FOOD_MATRIX
from app.schemas.weather import WeatherInfo, WeatherRecommendRequest, WeatherRecommendResponse
from app.schemas.recommendation import RecommendRequest
from app.core.recommender import recommend_restaurants

def get_realtime_weather(lat: float, lon: float):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            cw = resp.json().get("current_weather", {})
            temp = float(cw.get("temperature", 28.0))
            code = int(cw.get("weathercode", 0))
            return temp, code
    except Exception as e:
        print(f"Lỗi Open-Meteo API: {e}")
    return 28.0, 0

async def process_weather_recommendation(request_data: WeatherRecommendRequest) -> WeatherRecommendResponse:
    lat = 10.7769
    lon = 106.7009
    if request_data.user_gps and len(request_data.user_gps) == 2:
        lat, lon = request_data.user_gps[0], request_data.user_gps[1]
        
    temp, code = get_realtime_weather(lat, lon)
    if request_data.temperature is not None:
        temp = request_data.temperature
        
    rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]
    if code in rain_codes or temp < 24.0:
        w_type = "rainy"
    elif temp >= 30.0:
        w_type = "hot"
    else:
        w_type = "cool"
        
    meta = WEATHER_FOOD_MATRIX[w_type]
    target_tags = meta["tags"]
    
    w_info = WeatherInfo(
        temperature=round(temp, 1),
        condition_text=meta["condition_text"],
        condition_code=code,
        banner_title=meta["banner_title"].format(temp=round(temp, 1)),
        banner_desc=meta["banner_desc"],
        weather_type=w_type
    )
    
    query = " ".join(target_tags[:5])
    rec_req = RecommendRequest(query=query, user_gps=[lat, lon])
    rec_res = recommend_restaurants(rec_req)
    
    scores_list = rec_res.get("scores", [])
    return WeatherRecommendResponse(
        weather=w_info,
        scores=scores_list
    )
