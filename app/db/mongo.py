import pandas as pd
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import MONGO_URI, DB_NAME, COLLECTION_NAME
from app.core.text_utils import clean_coordinate, clean_price, extract_district_from_address

# Global dataset & model state
df = None
tfidf_vectorizer = None

def load_dataset_from_mongo():
    global df, tfidf_vectorizer
    print("-> [MongoDB Loader] Đang kết nối và load dữ liệu từ MongoDB Atlas...")
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
            
            if 'lat' in temp_df.columns: 
                temp_df['lat'] = temp_df['lat'].apply(clean_coordinate)
            else: 
                temp_df['lat'] = 0.0
                
            if 'lon' in temp_df.columns: 
                temp_df['lon'] = temp_df['lon'].apply(clean_coordinate)
            else: 
                temp_df['lon'] = 0.0
            
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
            print(f"-> [MongoDB Loader] Load thành công {len(df)} quán ăn vào bộ nhớ AI.")
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
