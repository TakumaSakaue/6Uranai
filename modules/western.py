"""
西洋占星術による占いモジュール
"""

from skyfield.api import load, Topos, Loader
from skyfield.framelib import ecliptic_frame
from datetime import datetime, time, timezone, timedelta
import pytz
import os

# --- グローバル変数 (効率化のため) ---
_ts = None
_eph = None
_loader = None

# --- 初期化関数 ---
def _initialize_skyfield(data_path='.'):
    """Skyfieldのロード処理を初期化時に行う"""
    global _ts, _eph, _loader
    if _ts is None or _eph is None:
        # Loaderを使ってデータファイルのパスを指定可能にする
        _loader = Loader(data_path, verbose=False) # verbose=Trueでダウンロード状況表示
        _ts = _loader.timescale()
        # DE421は多くの用途に適しているが、より新しいもの(例: DE440)も利用可能
        # ファイルが存在しない場合はダウンロードされる
        _eph = _loader('de421.bsp')
        print("Skyfield initialized.") # 初期化完了のログ

def _ensure_initialized():
    """Skyfieldが初期化されているか確認し、されていなければ初期化"""
    if _ts is None or _eph is None:
        # 環境変数などからデータパスを取得することも可能
        data_dir = os.environ.get("SKYFIELD_DATA_DIR", ".")
        os.makedirs(data_dir, exist_ok=True) # データディレクトリ作成
        _initialize_skyfield(data_dir)


# --- ヘルパー関数 ---
def _get_ecliptic_longitude(body, observer, skyfield_time):
    """指定した天体の黄経を計算する"""
    _ensure_initialized() # Skyfieldが初期化されているか確認
    astrometric = observer.at(skyfield_time).observe(body)
    # .apparent() を使うと光行差などを考慮した視位置になる
    ecliptic_position = astrometric.apparent().frame_latlon(ecliptic_frame)
    # 黄経 (longitude) を返す。0-360度の範囲にする
    return ecliptic_position[1].degrees % 360

def _get_zodiac_name(longitude):
    """黄経から星座名を返す"""
    # 星座の開始角度 (春分点が牡羊座0度)
    zodiac_signs = [
        ('牡羊座', 0), ('牡牛座', 30), ('双子座', 60), ('蟹座', 90),
        ('獅子座', 120), ('乙女座', 150), ('天秤座', 180), ('蠍座', 210),
        ('射手座', 240), ('山羊座', 270), ('水瓶座', 300), ('魚座', 330),
    ]
    # 角度がどの範囲に入るか判定
    for i in range(len(zodiac_signs)):
        sign, start_long = zodiac_signs[i]
        # 次の星座の開始角度（魚座の場合は360度）
        end_long = zodiac_signs[(i + 1) % 12][1] if i < 11 else 360
        # 角度が範囲内かチェック (魚座の場合は 330 <= long < 360)
        if start_long <= longitude < end_long:
            return sign
        # 魚座の特殊ケース (360度ぴったりの場合)
        if sign == '魚座' and longitude == 360.0:
            return sign
    # 通常ここには到達しない
    return "不明"

# --- APIから呼び出すメイン関数 ---
def calculate_astrology(birth_year, birth_month, birth_day):
    """
    生年月日から太陽星座と月星座を計算する関数

    Args:
        birth_year (int): 生まれた年（西暦）
        birth_month (int): 生まれた月（1～12）
        birth_day (int): 生まれた日（1～31）

    Returns:
        dict: {"sun_sign": 太陽星座名, "moon_sign": 月星座名} or None (エラー時)
    """
    try:
        _ensure_initialized() # Skyfieldが初期化されているか確認

        # --- 時刻の設定 (出生時間が不明なため、日本時間正午で計算) ---
        # タイムゾーンを日本時間 (JST, UTC+9) に設定
        jst = pytz.timezone('Asia/Tokyo')
        # 正午のdatetimeオブジェクトを作成
        local_dt = datetime(birth_year, birth_month, birth_day, 12, 0, 0)
        # タイムゾーン情報を付与
        local_dt_aware = jst.localize(local_dt)
        # UTCに変換
        utc_dt = local_dt_aware.astimezone(pytz.utc)

        # Skyfield用の時刻オブジェクトを作成
        t = _ts.utc(utc_dt)

        # --- 天体データの取得 ---
        earth = _eph['earth']
        moon = _eph['moon']
        sun = _eph['sun']

        # --- 観測地点の設定 (地球の中心から見た位置で計算するのが一般的) ---
        # 地心座標系 (Geocentric) を使用
        observer = earth

        # --- 太陽と月の黄経を計算 ---
        sun_longitude = _get_ecliptic_longitude(sun, observer, t)
        moon_longitude = _get_ecliptic_longitude(moon, observer, t)

        # --- 星座名を判定 ---
        sun_sign = _get_zodiac_name(sun_longitude)
        moon_sign = _get_zodiac_name(moon_longitude)

        if sun_sign == "不明" or moon_sign == "不明":
             raise ValueError("星座の判定に失敗しました。")

        return {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign
            # "sun_longitude": sun_longitude, # デバッグ用に黄経を含めても良い
            # "moon_longitude": moon_longitude
        }

    except Exception as e:
        print(f"西洋占星術計算エラー: {e}")
        # エラー発生時はNoneを返す
        return None

# --- 単体テスト用のコード ---
if __name__ == '__main__':
    # Skyfieldのデータファイルを保存するディレクトリを指定 (例: カレントディレクトリ下の 'skyfield-data')
    data_dir = 'skyfield-data'
    os.makedirs(data_dir, exist_ok=True)
    _initialize_skyfield(data_dir) # 初期化

    # 例: 1990年4月15日生まれ
    year, month, day = 1990, 4, 15
    result = calculate_astrology(year, month, day)
    if result:
        print(f"{year}年{month}月{day}日生まれ (日本時間正午)")
        print(f"  太陽星座: {result['sun_sign']}")
        print(f"  月星座: {result['moon_sign']}")
    else:
        print("計算に失敗しました。")

    # 例: 2000年1月1日生まれ
    year, month, day = 2000, 1, 1
    result = calculate_astrology(year, month, day)
    if result:
        print(f"{year}年{month}月{day}日生まれ (日本時間正午)")
        print(f"  太陽星座: {result['sun_sign']}")
        print(f"  月星座: {result['moon_sign']}")
    else:
        print("計算に失敗しました。")

    # 実行後、Loaderを閉じる (必須ではないが、リソース解放のため)
    if _loader:
        _loader.close() 