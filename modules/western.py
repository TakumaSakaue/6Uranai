"""
西洋占星術の計算モジュール
"""
from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from datetime import datetime
import pytz
import os

# グローバル変数（効率化のため）
_ts = None
_eph = None
_tokyo = None

# 初期化関数
def _initialize_skyfield(data_path='.'):
    """Skyfieldのロード処理を初期化時に行う"""
    global _ts, _eph, _tokyo
    if _ts is None or _eph is None:
        # データディレクトリの作成
        os.makedirs(data_path, exist_ok=True)
        print(f"Skyfieldデータディレクトリ: {data_path}")
        
        # Skyfieldの初期化
        _ts = load.timescale()
        _eph = load('de421.bsp')
        earth = _eph['earth']
        _tokyo = earth + Topos(latitude_degrees=35.6895, longitude_degrees=139.6917)
        print("Skyfield initialized.")

def _ensure_initialized():
    """Skyfieldが初期化されているか確認し、されていなければ初期化"""
    if _ts is None or _eph is None:
        data_dir = os.environ.get("SKYFIELD_DATA_DIR", "skyfield-data")
        _initialize_skyfield(data_dir)

# 黄経を取得する関数
def _get_ecliptic_longitude(body, t):
    """指定した天体の黄経を計算する"""
    astrometric = _tokyo.at(t).observe(body)
    ecliptic_position = astrometric.frame_latlon(ecliptic_frame)
    return ecliptic_position[1].degrees % 360

# 星座リスト
ZODIAC_SIGNS = [
    ('牡羊座', 0, 30),
    ('牡牛座', 30, 60),
    ('双子座', 60, 90),
    ('蟹座', 90, 120),
    ('獅子座', 120, 150),
    ('乙女座', 150, 180),
    ('天秤座', 180, 210),
    ('蠍座', 210, 240),
    ('射手座', 240, 270),
    ('山羊座', 270, 300),
    ('水瓶座', 300, 330),
    ('魚座', 330, 360),
]

# 星座判定関数
def _get_zodiac_name(longitude):
    """黄経から星座名を返す"""
    for sign, start, end in ZODIAC_SIGNS:
        if start <= longitude < end:
            return sign
    return "不明"

def calculate_western_astrology(year, month, day):
    """
    西洋占星術の結果を計算する
    
    Args:
        year (int): 生年
        month (int): 生月
        day (int): 生日
        
    Returns:
        dict: 西洋占星術の結果
    """
    try:
        # Skyfieldの初期化
        _ensure_initialized()
        
        # 出生時間が不明なので正午に固定（日本時間12:00）
        local_dt = datetime(year, month, day, 12, 0)
        jst = pytz.timezone('Asia/Tokyo')
        local_dt = jst.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)
        
        # Skyfield用の時刻オブジェクトを作成
        t = _ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
        
        # 天体データの取得
        moon = _eph['moon']
        sun = _eph['sun']
        
        # 黄経を取得
        moon_long = _get_ecliptic_longitude(moon, t)
        sun_long = _get_ecliptic_longitude(sun, t)
        
        # 星座判定
        moon_sign = _get_zodiac_name(moon_long)
        sun_sign = _get_zodiac_name(sun_long)
        
        # 結果を辞書形式で返す
        result = {
            "moon_sign": moon_sign,  # 月星座
            "sun_sign": sun_sign,  # 太陽星座
            "moon_longitude": moon_long,  # 月の黄経
            "sun_longitude": sun_long,  # 太陽の黄経
            "interpretation": f"あなたの月星座は「{moon_sign}」（黄経: {moon_long:.2f}°）です。\nあなたの太陽星座は「{sun_sign}」（黄経: {sun_long:.2f}°）です。"
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"西洋占星術の計算中にエラーが発生しました: {str(e)}"
        } 