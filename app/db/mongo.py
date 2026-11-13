import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import MONGO_URI, DB_NAME, COLLECTION_NAME
from app.core.text_utils import clean_coordinate, clean_price, extract_district_from_address

# Global dataset & model state
df = None
tfidf_vectorizer = None

def extract_coords_from_row(row):
    """
    [TASK-P0-01] Ưu tiên trích xuất tọa độ từ chuẩn GeoJSON location: { type: 'Point', coordinates: [lon, lat] }
    Fallback sang các trường lat/lon số phẳng nếu chưa migrate.
    """
    loc = row.get('location')
    if isinstance(loc, dict) and 'coordinates' in loc and isinstance(loc['coordinates'], (list, tuple)) and len(loc['coordinates']) >= 2:
        try:
            lon = float(loc['coordinates'][0])
            lat = float(loc['coordinates'][1])
            if lat != 0.0 and lon != 0.0:
                return lat, lon
        except (ValueError, TypeError):
            pass

    lat = clean_coordinate(row.get('lat', 0.0))
    lon = clean_coordinate(row.get('lon', 0.0))
    return lat, lon

def load_dataset_from_mongo():
    global df, tfidf_vectorizer
    print("-> [MongoDB Loader] Đang kết nối và load dữ liệu từ MongoDB...")
    if not MONGO_URI:
        print("-> [MongoDB Loader] CẢNH BÁO BẢO MẬT: MONGODB_URI chưa được thiết lập trong biến môi trường. Khởi tạo dataset rỗng.")
        df = pd.DataFrame(columns=['id', 'name', 'tags', 'rating', 'price', 'lat', 'lon', 'district', 'address'])
        tfidf_vectorizer = TfidfVectorizer()
        return False

    try:
        client = MongoClient(MONGO_URI)
        collection = client[DB_NAME][COLLECTION_NAME]
        data_list = list(collection.find({}))
        
        if not data_list:
            df = pd.DataFrame(columns=['id', 'name', 'tags', 'rating', 'price', 'lat', 'lon', 'district', 'address'])
            tfidf_vectorizer = TfidfVectorizer()
        else:
            temp_df = pd.DataFrame(data_list)
            temp_df['id'] = temp_df['_id'].astype(str)
            rename_map = {'tenQuan': 'name', 'diemTrungBinh': 'rating', 'giaCa': 'price', 'diaChi': 'address'}
            temp_df.rename(columns=rename_map, inplace=True)
            
            temp_df['tags'] = temp_df['tags'].apply(lambda x: " ".join(x) if isinstance(x, list) else str(x)).fillna('')
            
            # Trích xuất tọa độ GeoJSON / lat-lon
            coords = temp_df.apply(extract_coords_from_row, axis=1)
            temp_df['lat'] = [c[0] for c in coords]
            temp_df['lon'] = [c[1] for c in coords]
            
            if 'price' not in temp_df.columns:
                temp_df['price'] = 0.0
            else:
                temp_df['price'] = temp_df['price'].apply(clean_price)
                
            if 'address' not in temp_df.columns:
                temp_df['address'] = ''
                
            temp_df['district'] = temp_df['address'].apply(extract_district_from_address)
            
            df = temp_df
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_vectorizer.fit(df['tags'])
            print(f"-> [MongoDB Loader] Load thành công {len(df)} quán ăn vào bộ nhớ AI (GeoJSON Aware).")
            return True
    except Exception as e:
        print(f"!!! Lỗi Critical khi load DB: {e}")
        df = pd.DataFrame()
        tfidf_vectorizer = None
        return False

def get_dataset():
    global df
    if df is None or df.empty:
        load_dataset_from_mongo()
    return df

def get_vectorizer():
    global tfidf_vectorizer
    if tfidf_vectorizer is None:
        load_dataset_from_mongo()
    return tfidf_vectorizer
