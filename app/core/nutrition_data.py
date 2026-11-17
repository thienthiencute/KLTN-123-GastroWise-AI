"""
GastroWise AI Microservice - Vietnamese Food Nutrition Database
Pure Python dictionary defining calories, macronutrients and serving descriptions
for Vietnamese dishes, decoupled from computer vision dependencies.
"""

from typing import Dict, Any

VIETNAMESE_FOOD_NUTRITION: Dict[str, Dict[str, Any]] = {
    'bánh mì': {'calories': 385, 'protein_g': 12.5, 'carbs_g': 55.0, 'fat_g': 14.0, 'serving_desc': '1 ổ bánh mì kẹp thịt chả'},
    'banh mi': {'calories': 385, 'protein_g': 12.5, 'carbs_g': 55.0, 'fat_g': 14.0, 'serving_desc': '1 ổ bánh mì kẹp thịt chả'},
    'phở': {'calories': 460, 'protein_g': 24.0, 'carbs_g': 62.0, 'fat_g': 11.5, 'serving_desc': '1 tô phở bò tái chín'},
    'pho': {'calories': 460, 'protein_g': 24.0, 'carbs_g': 62.0, 'fat_g': 11.5, 'serving_desc': '1 tô phở bò tái chín'},
    'bún': {'calories': 440, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 12.0, 'serving_desc': '1 tô bún nước'},
    'bun': {'calories': 440, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 12.0, 'serving_desc': '1 tô bún nước'},
    'bún bò huế': {'calories': 530, 'protein_g': 28.0, 'carbs_g': 60.0, 'fat_g': 18.0, 'serving_desc': '1 tô bún bò Huế đầy đủ'},
    'bun bo hue': {'calories': 530, 'protein_g': 28.0, 'carbs_g': 60.0, 'fat_g': 18.0, 'serving_desc': '1 tô bún bò Huế đầy đủ'},
    'bún chả': {'calories': 510, 'protein_g': 25.0, 'carbs_g': 65.0, 'fat_g': 15.0, 'serving_desc': '1 suất bún chả nướng than hoa'},
    'bún đậu mắm tôm': {'calories': 580, 'protein_g': 26.0, 'carbs_g': 54.0, 'fat_g': 24.0, 'serving_desc': '1 mẹt bún đậu thập cẩm'},
    'bún riêu': {'calories': 420, 'protein_g': 18.0, 'carbs_g': 56.0, 'fat_g': 13.0, 'serving_desc': '1 tô bún riêu cua đồng'},
    'cơm tấm': {'calories': 650, 'protein_g': 32.0, 'carbs_g': 78.0, 'fat_g': 21.0, 'serving_desc': '1 đĩa cơm sườn bì chả'},
    'com tam': {'calories': 650, 'protein_g': 32.0, 'carbs_g': 78.0, 'fat_g': 21.0, 'serving_desc': '1 đĩa cơm sườn bì chả'},
    'cơm gà': {'calories': 590, 'protein_g': 34.0, 'carbs_g': 68.0, 'fat_g': 18.0, 'serving_desc': '1 đĩa cơm gà xé / luộc'},
    'gỏi cuốn': {'calories': 180, 'protein_g': 9.0, 'carbs_g': 28.0, 'fat_g': 2.5, 'serving_desc': '3 cuốn tôm thịt chấm tương'},
    'goi cuon': {'calories': 180, 'protein_g': 9.0, 'carbs_g': 28.0, 'fat_g': 2.5, 'serving_desc': '3 cuốn tôm thịt chấm tương'},
    'bột chiên': {'calories': 480, 'protein_g': 11.0, 'carbs_g': 52.0, 'fat_g': 24.0, 'serving_desc': '1 đĩa bột chiên 2 trứng'},
    'bot chien': {'calories': 480, 'protein_g': 11.0, 'carbs_g': 52.0, 'fat_g': 24.0, 'serving_desc': '1 đĩa bột chiên 2 trứng'},
    'bánh xèo': {'calories': 420, 'protein_g': 14.0, 'carbs_g': 46.0, 'fat_g': 20.0, 'serving_desc': '1 cái bánh xèo giòn rụm'},
    'bánh cuốn': {'calories': 320, 'protein_g': 12.0, 'carbs_g': 48.0, 'fat_g': 8.0, 'serving_desc': '1 đĩa bánh cuốn nóng chả lụa'},
    'hủ tiếu': {'calories': 450, 'protein_g': 21.0, 'carbs_g': 64.0, 'fat_g': 10.0, 'serving_desc': '1 tô hủ tiếu Nam Vang'},
    'mì quảng': {'calories': 480, 'protein_g': 22.0, 'carbs_g': 60.0, 'fat_g': 14.0, 'serving_desc': '1 tô mì Quảng tôm thịt'},
    'nem nướng': {'calories': 390, 'protein_g': 19.0, 'carbs_g': 35.0, 'fat_g': 16.0, 'serving_desc': '1 phần nem nướng bánh tráng'},
    'cà phê sữa đá': {'calories': 140, 'protein_g': 2.5, 'carbs_g': 22.0, 'fat_g': 4.0, 'serving_desc': '1 ly cà phê sữa đá pha phin'},
    'chè thái': {'calories': 280, 'protein_g': 3.0, 'carbs_g': 52.0, 'fat_g': 7.0, 'serving_desc': '1 ly chè Thái sầu riêng'},
}

