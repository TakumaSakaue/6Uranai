"""
宿曜占いの計算を行うモジュール
"""
import re
from datetime import datetime
import pytz
import koyomi

# 宿曜（星宿）の名称リスト（27宿）
mansion_names = [
    "昴宿", "畢宿", "觜宿", "参宿", "井宿", "鬼宿", "柳宿", "星宿",
    "張宿", "翼宿", "軫宿", "角宿", "亢宿", "氐宿", "房宿", "心宿",
    "尾宿", "箕宿", "斗宿", "女宿", "虚宿", "危宿", "室宿", "壁宿",
    "奎宿", "婁宿", "胃宿"
]

def extract_old_day(kyureki_str):
    """旧暦表示文字列から「日」の部分を抽出する関数"""
    match = re.search(r"(\d+)日", kyureki_str)
    if match:
        return int(match.group(1))
    else:
        return None

def extract_old_month(kyureki_str):
    """旧暦表示文字列から「月」の部分を抽出する関数"""
    match = re.search(r"年(\d+)月", kyureki_str)
    if match:
        return int(match.group(1))
    else:
        return None

def get_base_for_month(lunar_month):
    """旧暦月ごとのキャリブレーション値（base値）のテーブル"""
    base_table = {
        1: 22, 2: 24, 3: 26, 4: 1, 5: 3, 6: 5,
        7: 8, 8: 11, 9: 13, 10: 15, 11: 18, 12: 20
    }
    return base_table.get(lunar_month, 18)

def calc_mansion_from_old_date(lunar_day, lunar_month):
    """宿曜を旧暦の日および旧暦月から算出する関数"""
    base = get_base_for_month(lunar_month)
    index = (lunar_day - 1 + base) % 27
    return mansion_names[index], base

def calculate_sukuyo(year, month, day):
    """
    西暦日付から宿曜を計算
    
    Args:
        year (int): 西暦年
        month (int): 月
        day (int): 日
    
    Returns:
        dict: 計算結果を含む辞書
    """
    try:
        # koyomi ライブラリで旧暦結果を取得
        lunar_date = koyomi.to_lunar_date(year, month, day)
        
        # 旧暦の月日を取得
        old_day = lunar_date.day
        lunar_month = lunar_date.month
        
        # 宿曜を計算
        mansion, base = calc_mansion_from_old_date(old_day, lunar_month)
        
        return {
            "mansion": mansion
        }
        
    except Exception as e:
        return {
            "error": f"計算エラー: {str(e)}",
            "mansion": "不明"
        } 