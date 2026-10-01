import os

# --- MONGODB CONFIG ---
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://thienthien:GastroWise2026@cluster01.adts0oq.mongodb.net/gastrowise?appName=Cluster01"
)
DB_NAME = "gastrowise"
COLLECTION_NAME = "restaurants"

# --- TAG KNOWLEDGE BASE ---
TAG_KNOWLEDGE_BASE = {
    # Về không gian/nhu cầu
    'lãng mạn': 'hẹn hò', 'sang chảnh': 'sang trọng', 'đắt tiền': 'sang trọng', 'luxury': 'sang trọng',
    'thoải mái': 'yên tĩnh', 'nhanh gọn': 'nhanh', 'tụ tập': 'nhậu', 'nhậu nhẹt': 'nhậu',
    'bình dân': 'rẻ', 'hạt dẻ': 'rẻ', 'sinh viên': 'rẻ',
    'mát mẻ': 'máy lạnh', 'điều hòa': 'máy lạnh',
    'view đẹp': 'đẹp', 'sống ảo': 'đẹp',
    
    # Về món ăn (Vùng miền)
    'đồng quê': 'cơm việt', 'cơm bắc': 'cơm việt', 'cơm niêu': 'cơm việt',
    'đặc sản huế': 'bún bò huế', 'món huế': 'bún bò huế',
    'đặc sản hà nội': 'bún chả', 'phở bắc': 'phở',
    'đặc sản sài gòn': 'cơm tấm', 
    'đồ nướng': 'nướng', 'bbq': 'nướng',
    'hải sản tươi sống': 'hải sản'
}

# --- EN-VI MAPPING ---
EN_VI_MAPPING = {
    # -- Món nước --
    'beef noodle': 'bún bò', 'beef noodle soup': 'bún bò', 'bun bo': 'bún bò',
    'pho': 'phở', 'noodle soup': 'phở', 'chicken noodle': 'phở gà',
    'crab noodle': 'bún riêu', 'snail noodle': 'bún ốc',
    'fish noodle': 'bún cá',
    'hu tieu': 'hủ tiếu', 'vermicelli': 'bún', 'glass noodle': 'miến',
    'ramen': 'mì nhật', 'udon': 'mì udon',
    
    # -- Cơm & Món mặn --
    'broken rice': 'cơm tấm', 'com tam': 'cơm tấm', 'pork chop rice': 'cơm sườn',
    'chicken rice': 'cơm gà', 'fried rice': 'cơm chiên',
    'rice': 'cơm', 'sticky rice': 'xôi',
    'braised pork': 'thịt kho', 'catfish': 'cá kho',
    
    # -- Bánh & Ăn vặt --
    'bread': 'bánh mì', 'baguette': 'bánh mì', 'sandwich': 'bánh mì',
    'pancake': 'bánh xèo', 'sizzling cake': 'bánh xèo',
    'spring roll': 'gỏi cuốn', 'summer roll': 'gỏi cuốn', 'fresh roll': 'gỏi cuốn',
    'fried roll': 'chả giò', 'egg roll': 'chả giò',
    'steamed roll': 'bánh cuốn', 'dumpling': 'há cảo', 'dimsum': 'dimsum',
    'snack': 'ăn vặt', 'street food': 'vỉa hè',
    'banh mi': 'bánh mì',
    'banhmi': 'bánh mì',
    'banh-mi': 'bánh mì',
    'bun bo hue': 'bún bò huế',
    'bun dau mam tom': 'bún đậu mắm tôm',
    'goi-cuon': 'gỏi cuốn',
    'Goi-Cuon': 'gỏi cuốn',
    'Bot Chien': 'bột chiên',
    
    # -- Lẩu & Nướng --
    'hotpot': 'lẩu', 'thai hotpot': 'lẩu thái',
    'bbq': 'nướng', 'grilled': 'nướng', 'steak': 'bít tết', 'beefsteak': 'bít tết',
    
    # -- Nguyên liệu --
    'seafood': 'hải sản', 'fish': 'cá', 'crab': 'cua', 'shrimp': 'tôm', 
    'snail': 'ốc', 'clam': 'nghêu', 'oyster': 'hàu',
    'beef': 'bò', 'chicken': 'gà', 'pork': 'heo', 'duck': 'vịt', 'goat': 'dê',
    'vegetarian': 'chay', 'vegan': 'chay', 'tofu': 'đậu hũ',
    
    # -- Đồ uống & Tráng miệng --
    'coffee': 'cà phê', 'milk coffee': 'cà phê sữa', 'egg coffee': 'cà phê trứng',
    'tea': 'trà', 'milk tea': 'trà sữa', 'bubble tea': 'trà sữa',
    'juice': 'nước ép', 'smoothie': 'sinh tố', 'beer': 'bia',
    'dessert': 'tráng miệng', 'sweet soup': 'chè', 'ice cream': 'kem', 'cake': 'bánh ngọt',
    
    # -- Tính chất --
    'delicious': 'ngon', 'yummy': 'ngon', 'tasty': 'ngon', 'good': 'ngon', 'best': 'ngon nhất',
    'cheap': 'rẻ', 'budget': 'rẻ', 'reasonable': 'rẻ', 'affordable': 'rẻ',
    'expensive': 'sang trọng', 'luxury': 'sang trọng', 'fine dining': 'sang trọng',
    'near': 'gần', 'nearby': 'gần', 'closest': 'gần',
    'spicy': 'cay', 'hot': 'cay',
    'nice view': 'đẹp', 'air conditioner': 'máy lạnh', 'ac': 'máy lạnh',
    
    # -- Thời gian & Địa điểm --
    'late night': 'ăn đêm', 'night': 'đêm', 'midnight': 'đêm',
    'morning': 'sáng', 'breakfast': 'sáng',
    'lunch': 'trưa', 'noon': 'trưa',
    'dinner': 'tối',
    'district': 'quận', 'city': 'thành phố', 'hcmc': 'tphcm', 'saigon': 'sài gòn'
}

# --- LOCATION NAMES ---
LOCATION_NAMES = {
    # --- TP. HỒ CHÍ MINH ---
    'quận 1': 'Quận 1', 'q1': 'Quận 1', 
    'quận 2': 'Quận 2', 'q2': 'Quận 2',
    'quận 3': 'Quận 3', 'q3': 'Quận 3', 
    'quận 4': 'Quận 4', 'q4': 'Quận 4',
    'quận 5': 'Quận 5', 'q5': 'Quận 5', 
    'quận 6': 'Quận 6', 'q6': 'Quận 6',
    'quận 7': 'Quận 7', 'q7': 'Quận 7', 
    'quận 8': 'Quận 8', 'q8': 'Quận 8',
    'quận 9': 'Quận 9', 'q9': 'Quận 9', 
    'quận 10': 'Quận 10', 'q10': 'Quận 10',
    'quận 11': 'Quận 11', 'q11': 'Quận 11', 
    'quận 12': 'Quận 12', 'q12': 'Quận 12',
    'bình thạnh': 'Bình Thạnh', 'bt': 'Bình Thạnh',
    'phú nhuận': 'Phú Nhuận', 'pn': 'Phú Nhuận',
    'gò vấp': 'Gò Vấp', 'gv': 'Gò Vấp',
    'tân bình': 'Tân Bình', 'tb': 'Tân Bình',
    'tân phú': 'Tân Phú', 'tp': 'Tân Phú',
    'bình tân': 'Bình Tân', 
    'thủ đức': 'Thủ Đức', 'tđ': 'Thủ Đức',
    'sài gòn': 'TPHCM', 'hcm': 'TPHCM', 'tphcm': 'TPHCM',
    'bình chánh': 'Bình Chánh', 'hóc môn': 'Hóc Môn', 
    'củ chi': 'Củ Chi', 'nhà bè': 'Nhà Bè', 'cần giờ': 'Cần Giờ',

    # --- HÀ NỘI ---
    'hà nội': 'Hà Nội', 'hn': 'Hà Nội', 'thủ đô': 'Hà Nội',
    'ba đình': 'Ba Đình', 'bđ': 'Ba Đình',
    'hoàn kiếm': 'Hoàn Kiếm', 'hk': 'Hoàn Kiếm',
    'tây hồ': 'Tây Hồ', 
    'long biên': 'Long Biên', 'lb': 'Long Biên',
    'cầu giấy': 'Cầu Giấy', 'cg': 'Cầu Giấy',
    'đống đa': 'Đống Đa', 'đđ': 'Đống Đa',
    'hai bà trưng': 'Hai Bà Trưng', 'hbt': 'Hai Bà Trưng',
    'hoàng mai': 'Hoàng Mai', 'hm': 'Hoàng Mai',
    'thanh xuân': 'Thanh Xuân', 'tx': 'Thanh Xuân',
    'sóc sơn': 'Sóc Sơn', 'đông anh': 'Đông Anh', 'gia lâm': 'Gia Lâm',
    'nam từ liêm': 'Nam Từ Liêm', 'ntl': 'Nam Từ Liêm',
    'bắc từ liêm': 'Bắc Từ Liêm', 'btl': 'Bắc Từ Liêm',
    'hà đông': 'Hà Đông', 'hđ': 'Hà Đông',
    'sơn tây': 'Sơn Tây', 'ba vì': 'Ba Vì', 'phúc thọ': 'Phúc Thọ',
    'đan phượng': 'Đan Phượng', 'hoài đức': 'Hoài Đức', 'quốc oai': 'Quốc Oai',
    'thạch thất': 'Thạch Thất', 'chương mỹ': 'Chương Mỹ', 'thanh oai': 'Thanh Oai',
    'thường tín': 'Thường Tín', 'phú xuyên': 'Phú Xuyên', 'ứng hòa': 'Ứng Hòa',
    'mỹ đức': 'Mỹ Đức', 'mê linh': 'Mê Linh', 'thanh trì': 'Thanh Trì',

    # --- ĐÀ NẴNG ---
    'đà nẵng': 'Đà Nẵng', 'đn': 'Đà Nẵng', 'dn': 'Đà Nẵng',
    'hải châu': 'Hải Châu', 'hc': 'Hải Châu',
    'thanh khê': 'Thanh Khê', 'tk': 'Thanh Khê',
    'sơn trà': 'Sơn Trà', 'st': 'Sơn Trà',
    'ngũ hành sơn': 'Ngũ Hành Sơn', 'nhs': 'Ngũ Hành Sơn',
    'liên chiểu': 'Liên Chiểu', 'lc': 'Liên Chiểu',
    'cẩm lệ': 'Cẩm Lệ', 'cl': 'Cẩm Lệ',
    'hòa vang': 'Hòa Vang', 'hoàng sa': 'Hoàng Sa',

    # --- CẦN THƠ ---
    'cần thơ': 'Cần Thơ', 'ct': 'Cần Thơ', 'tay do': 'Cần Thơ', 'tây đô': 'Cần Thơ',
    'ninh kiều': 'Ninh Kiều', 'nk': 'Ninh Kiều',
    'cái răng': 'Cái Răng', 'cr': 'Cái Răng',
    'bình thủy': 'Bình Thủy',
    'ô môn': 'Ô Môn', 'thốt nốt': 'Thốt Nốt',
    'phong điền': 'Phong Điền',

    # --- HẢI PHÒNG ---
    'hải phòng': 'Hải Phòng', 'hp': 'Hải Phòng', 'đất cảng': 'Hải Phòng',
    'ngô quyền': 'Ngô Quyền', 'lê chân': 'Lê Chân', 'hồng bàng': 'Hồng Bàng',
    'hải an': 'Hải An', 'kiến an': 'Kiến An', 'đồ sơn': 'Đồ Sơn', 'dương kinh': 'Dương Kinh',
    'thủy nguyên': 'Thủy Nguyên', 'an dương': 'An Dương', 'an lão': 'An Lão',
    'cát hải': 'Cát Hải', 'cát bà': 'Cát Bà',

    # --- KHÁNH HÒA ---
    'khánh hòa': 'Khánh Hòa', 'kh': 'Khánh Hòa',
    'nha trang': 'Nha Trang', 'nt': 'Nha Trang',
    'cam ranh': 'Cam Ranh', 'ninh hòa': 'Ninh Hòa',
    'vạn ninh': 'Vạn Ninh', 'diên khánh': 'Diên Khánh', 'cam lâm': 'Cam Lâm',

    # --- BÀ RỊA - VŨNG TÀU ---
    'bà rịa vũng tàu': 'Vũng Tàu', 'brvt': 'Vũng Tàu',
    'vũng tàu': 'Vũng Tàu', 'vt': 'Vũng Tàu',
    'bà rịa': 'Bà Rịa',
    'phú mỹ': 'Phú Mỹ', 'châu đức': 'Châu Đức', 'xuyên mộc': 'Xuyên Mộc',
    'long điền': 'Long Điền', 'đất đỏ': 'Đất Đỏ', 'côn đảo': 'Côn Đảo',

    # --- LÂM ĐỒNG ---
    'lâm đồng': 'Lâm Đồng', 'ld': 'Lâm Đồng',
    'đà lạt': 'Đà Lạt', 'dl': 'Đà Lạt', 
    'thành phố ngàn hoa': 'Đà Lạt', 'xứ sở sương mù': 'Đà Lạt',
    'bảo lộc': 'Bảo Lộc', 'bl': 'Bảo Lộc',
    'đức trọng': 'Đức Trọng',
    'di linh': 'Di Linh',
    'lạc dương': 'Lạc Dương',
    'đơn dương': 'Đơn Dương', 
    'lâm hà': 'Lâm Hà',
}

MAJOR_CITIES = ['Hà Nội', 'TPHCM', 'Đà Nẵng']

CANDIDATE_TAGS = [
    # -- Món Nước --
    'bún bò', 'bún bò huế', 'bún riêu', 'bún mắm', 'bún chả', 'bún thịt nướng', 'bún đậu', 
    'bún cá', 'bún mọc', 'bún thái', 'bún ốc', 'bún',
    'phở', 'phở bò', 'phở gà', 'phở cuốn',
    'hủ tiếu', 'hủ tiếu nam vang', 'hủ tiếu gõ', 'hủ tiếu mực',
    'bánh canh', 'bánh canh cua', 'bánh canh ghẹ', 'bánh canh cá lóc',
    'mì', 'mì quảng', 'mì vịt tiềm', 'mì ý', 'mì cay', 'mì xào', 'mì trộn', 'ramen', 'udon',
    'miến', 'miến gà', 'miến lươn', 'miến xào',
    'nui', 'nui xào', 'bò kho', 'lagu', 'cà ri', 'cháo', 'cháo lòng', 'cháo ếch', 'súp',

    # -- Cơm --
    'cơm tấm', 'cơm sườn', 'cơm gà', 'cơm gà xối mỡ', 'cơm niêu', 'cơm văn phòng', 
    'cơm chiên', 'cơm rang', 'cơm lam', 'cơm phần', 'cơm',
    'xôi', 'xôi gà', 'xôi mặn',
    
    # -- Món Mặn / Nhậu --
    'lẩu', 'lẩu thái', 'lẩu bò', 'lẩu gà', 'lẩu dê', 'lẩu hải sản', 'lẩu mắm', 'lẩu cá',
    'nướng', 'bbq', 'bò nướng', 'gà nướng', 'hải sản nướng', 'nem nướng',
    'bít tết', 'bò né', 'bò bít tết', 'steak',
    'hải sản', 'ốc', 'tôm', 'cua', 'ghẹ', 'hàu', 'mực', 'bạch tuộc',
    'gà rán', 'gà luộc', 'gà ủ muối', 'vịt quay', 'heo quay', 'phá lấu',
    'dê', 'cừu', 'ếch', 'lươn', 'bột chiên',
    
    # -- Bánh & Ăn vặt --
    'bánh mì', 'bánh mì chảo', 'bánh mì xíu mại',
    'bánh xèo', 'bánh khọt', 'bánh cuốn', 'bánh ướt', 'bánh bèo', 'bánh bột lọc', 'bánh nậm',
    'gỏi cuốn', 'bì cuốn', 'chả giò', 'nem rán',
    'pizza', 'hamburger', 'sushi', 'sashimi', 'dimsum', 'há cảo', 'xíu mại',
    'ăn vặt', 'bánh tráng trộn', 'cá viên chiên', 'xiên que', 'bắp xào', 'hột vịt lộn',
    
    # -- Đồ uống & Tráng miệng --
    'cà phê', 'cà phê sữa', 'cà phê trứng', 'cà phê vợt',
    'trà sữa', 'trà đào', 'trà chanh', 'trà',
    'sinh tố', 'nước ép', 'chè', 'kem', 'bingsu', 'tàu hũ', 'sữa chua', 'bánh ngọt',
    'bia', 'bia thủ công', 'rượu', 'pub', 'bar',
    
    # -- Phong cách / Quốc gia --
    'chay', 'thuần chay', 'healthy', 'eat clean',
    'hàn quốc', 'nhật bản', 'trung hoa', 'thái lan', 'âu', 'mỹ', 'ý',
    'vỉa hè', 'sang trọng', 'bình dân', 'gia đình', 'hẹn hò', 'nhậu', 'view đẹp',
    'máy lạnh', 'sân vườn', 'yên tĩnh', 'nhanh', 'mang đi', 'buffet',
    
    # -- Thời gian --
    'sáng', 'trưa', 'chiều', 'tối', 'đêm', 'ăn đêm', '24h'
]

PRIORITY_TAGS = ['đêm', 'sáng', 'trưa', 'chiều', 'tối', 'ăn đêm']
ADJECTIVE_TAGS = ['rẻ', 'gần', 'ngon', 'tốt', 'nhanh', 'đẹp', 'vỉa hè', 'sang trọng', 'yên tĩnh', 'nổi tiếng', 'nhất']

WEATHER_FOOD_MATRIX = {
    "rainy": {
        "tags": ["lẩu", "lẩu thái", "lẩu bò", "phở", "bún bò", "nướng", "bbq", "mì cay", "chè nóng", "súp", "bò kho", "cháo"],
        "condition_text": "Mưa rào / Trầm lắng",
        "banner_title": "🌧️ Trời đang mưa lạnh ({temp}°C)",
        "banner_desc": "Thời tiết lý tưởng để thưởng thức Lẩu Thái, Phở Nóng, Bún Bò & Nướng BBQ nghi ngút khói!"
    },
    "hot": {
        "tags": ["trà sữa", "sinh tố", "nước ép", "kem", "bingsu", "chè", "gỏi cuốn", "chay", "máy lạnh", "trà chanh", "bún", "cơm tấm"],
        "condition_text": "Trời nắng nóng",
        "banner_title": "☀️ Trời nắng nóng ({temp}°C)",
        "banner_desc": "Giải nhiệt ngay với Trà Sữa, Sinh Tố, Nước Ép tươi mát & các quán ăn có máy lạnh thoáng mát!"
    },
    "cool": {
        "tags": ["cà phê", "ăn vặt", "bánh mì", "cơm niêu", "bún chả", "pizza", "sushi", "vỉa hè", "trà"],
        "condition_text": "Thời tiết mát mẻ / Dễ chịu",
        "banner_title": "🌤️ Thời tiết dễ chịu ({temp}°C)",
        "banner_desc": "Thời điểm hoàn hảo để dạo phố, uống Cà Phê & thưởng thức các món ăn vặt thơm ngon!"
    }
}
