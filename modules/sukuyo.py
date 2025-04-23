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

def get_base_for_month(old_month):
    """月の基準値を取得（修正版）"""
    # 月の基準値テーブル（修正版）
    base_table = {
        1: 11,  # 正月
        2: 13,  # 2月
        3: 15,  # 3月
        4: 17,  # 4月
        5: 19,  # 5月
        6: 21,  # 6月
        7: 23,  # 7月
        8: 25,  # 8月
        9: 0,   # 9月
        10: 2,  # 10月
        11: 4,  # 11月
        12: 6   # 12月
    }
    
    base = base_table.get(old_month, 11)  # デフォルト値を11に設定
    print(f"月の基準値: 旧暦{old_month}月 = {base}")
    return base

def calc_mansion_from_old_date(old_month, old_day):
    """旧暦の月日から宿曜を計算"""
    # 月の基準値
    base = get_base_for_month(old_month)
    
    # 日付を調整（1から始まるように）
    adjusted_day = old_day
    
    # 宿曜の計算
    # 基準値に日数を加算し、27で割った余りを取得
    mansion_index = (base + adjusted_day) % 27
    
    # デバッグ情報
    print(f"宿曜計算の詳細:")
    print(f"月の基準値: {base}")
    print(f"調整後の日: {adjusted_day}")
    print(f"計算式: ({base} + {adjusted_day}) % 27 = {mansion_index}")
    
    return mansion_names[mansion_index]

def calculate_sukuyo(year, month, day):
    """宿曜を計算"""
    try:
        print(f"宿曜計算開始: {year}年{month}月{day}日")
        
        # 入力値の検証
        if not all(isinstance(x, int) for x in [year, month, day]):
            raise ValueError("年月日は整数である必要があります")
        
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("月は1-12、日は1-31の範囲である必要があります")
        
        # 旧暦に変換
        try:
            lunar_date = koyomi.to_lunar_date(year, month, day)
            print(f"旧暦変換結果: {lunar_date}")
            
            if not lunar_date:
                raise ValueError("旧暦変換に失敗しました")
            
            old_month = lunar_date[1]
            old_day = lunar_date[2]
            
            print(f"旧暦: {old_month}月{old_day}日")
            
            # 宿曜を計算
            mansion = calc_mansion_from_old_date(old_month, old_day)
            print(f"計算結果の宿曜: {mansion}")
            
            return {
                "mansion": mansion,
                "lunar_date": f"{old_month}月{old_day}日",
                "base": get_base_for_month(old_month),
                "debug": {
                    "input_date": f"{year}年{month}月{day}日",
                    "lunar_date": f"{old_month}月{old_day}日",
                    "calculation": "正常に計算完了"
                }
            }
            
        except Exception as e:
            print(f"旧暦変換エラー: {str(e)}")
            print(f"エラーの種類: {type(e).__name__}")
            import traceback
            print(f"スタックトレース: {traceback.format_exc()}")
            
            # フォールバック計算（修正版）
            print("フォールバック計算を開始")
            
            # 月の基準値を計算
            base = get_base_for_month(month)
            
            # 日付を1から始まるように調整
            adjusted_day = day - 1
            
            # 宿曜を計算
            mansion_index = (base + adjusted_day) % 27
            mansion = mansion_names[mansion_index]
            
            print(f"フォールバック計算結果:")
            print(f"月の基準値: {base}")
            print(f"調整後の日: {adjusted_day}")
            print(f"計算式: ({base} + {adjusted_day}) % 27 = {mansion_index}")
            print(f"宿曜: {mansion}")
            
            return {
                "mansion": mansion,
                "lunar_date": f"{month}月{day}日（フォールバック）",
                "base": base,
                "debug": {
                    "input_date": f"{year}年{month}月{day}日",
                    "calculation": "フォールバック計算を使用",
                    "base": base,
                    "adjusted_day": adjusted_day,
                    "mansion_index": mansion_index
                }
            }
            
    except Exception as e:
        print(f"宿曜計算エラー: {str(e)}")
        print(f"エラーの種類: {type(e).__name__}")
        import traceback
        print(f"スタックトレース: {traceback.format_exc()}")
        return {
            "mansion": "不明",
            "lunar_date": "不明",
            "base": 0,
            "debug": {
                "error": str(e),
                "error_type": type(e).__name__,
                "input": f"{year}年{month}月{day}日"
            }
        } 