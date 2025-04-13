"""
九星気学による占いモジュール
"""
from datetime import date

class KyuseiFortune:
    def __init__(self):
        self.kyusei_numbers = {
            1: "一白水星",
            2: "二黒土星",
            3: "三碧木星",
            4: "四緑木星",
            5: "五黄土星",
            6: "六白金星",
            7: "七赤金星",
            8: "八白土星",
            9: "九紫火星"
        }
        self.kyusei_dict_rev = {
            "一白水星": 1, "二黒土星": 2, "三碧木星": 3, "四緑木星": 4,
            "五黄土星": 5, "六白金星": 6, "七赤金星": 7, "八白土星": 8,
            "九紫火星": 9
        }

    def _get_honmei_sei(self, birth_year):
        """
        生まれた年から本命星（九星）を計算する関数
        
        Args:
            birth_year (int): 生まれた年（西暦）
            
        Returns:
            str: 本命星の名前
        """
        # 11から年数を引いて9で割った余りで計算する簡略式
        # (立春前の生まれは前年扱いにする必要あり - API側で考慮)
        remainder = (11 - (birth_year % 9)) % 9
        return self.kyusei_numbers.get(remainder, "不明")

    def _get_month_number(self, birth_month, birth_day):
        """
        生まれた月と日から月番号を計算する関数
        
        Args:
            birth_month (int): 生まれた月（1-12）
            birth_day (int): 生まれた日（1-31）
            
        Returns:
            int: 月番号（1-12）
        """
        # 九星気学の月は節入り日で変わる
        # 簡単のため、日付のみで判定（厳密には年によって節入り日は多少変動する）
        if (birth_month == 1 and birth_day < 6) or (birth_month == 12 and birth_day >= 7):
            return 11  # 12/7頃～1/5頃
        elif (birth_month == 2 and birth_day < 4) or (birth_month == 1 and birth_day >= 6):
            return 12  # 1/6頃～2/3頃
        elif (birth_month == 3 and birth_day < 6) or (birth_month == 2 and birth_day >= 4):
            return 1   # 2/4頃～3/5頃
        elif (birth_month == 4 and birth_day < 5) or (birth_month == 3 and birth_day >= 6):
            return 2   # 3/6頃～4/4頃
        elif (birth_month == 5 and birth_day < 6) or (birth_month == 4 and birth_day >= 5):
            return 3   # 4/5頃～5/5頃
        elif (birth_month == 6 and birth_day < 6) or (birth_month == 5 and birth_day >= 6):
            return 4   # 5/6頃～6/5頃
        elif (birth_month == 7 and birth_day < 8) or (birth_month == 6 and birth_day >= 6):
            return 5   # 6/6頃～7/7頃
        elif (birth_month == 8 and birth_day < 8) or (birth_month == 7 and birth_day >= 8):
            return 6   # 7/8頃～8/7頃
        elif (birth_month == 9 and birth_day < 8) or (birth_month == 8 and birth_day >= 8):
            return 7   # 8/8頃～9/7頃
        elif (birth_month == 10 and birth_day < 9) or (birth_month == 9 and birth_day >= 8):
            return 8   # 9/8頃～10/8頃
        elif (birth_month == 11 and birth_day < 8) or (birth_month == 10 and birth_day >= 9):
            return 9   # 10/9頃～11/7頃
        elif (birth_month == 12 and birth_day < 7) or (birth_month == 11 and birth_day >= 8):
            return 10  # 11/8頃～12/6頃
        else:
            # 通常ここには到達しないはず
            return 0  # エラーケース

    def _get_tsukimei_sei(self, honmei_sei_num, month_number):
        """
        本命星番号と月番号から月命星を計算する関数
        
        Args:
            honmei_sei_num (int): 本命星の番号（1-9）
            month_number (int): 月番号（1-12）
            
        Returns:
            str: 月命星の名前
        """
        tsukimei_base_num = 0
        # 本命星のグループ (簡易的な方法)
        if honmei_sei_num in [1, 4, 7]:  # 水・木・金グループ
            tsukimei_base_num = 8  # 2月(月番号1)は八白
        elif honmei_sei_num in [2, 5, 8]:  # 土グループ
            tsukimei_base_num = 2  # 2月(月番号1)は二黒
        elif honmei_sei_num in [3, 6, 9]:  # 木・金・火グループ
            tsukimei_base_num = 5  # 2月(月番号1)は五黄

        # 月番号に応じて逆行して月命星番号を決定
        # 2月(月番号1)を基準とする
        tsukimei_num = (tsukimei_base_num - (month_number - 1)) % 9
        if tsukimei_num <= 0:
            tsukimei_num += 9

        return self.kyusei_numbers.get(tsukimei_num, "不明")

    def calculate_kyusei(self, birth_year, birth_month, birth_day):
        """
        生年月日から九星気学の本命星と月命星を計算する関数

        Args:
            birth_year (int): 生まれた年（西暦）
            birth_month (int): 生まれた月（1～12）
            birth_day (int): 生まれた日（1～31）

        Returns:
            dict: {"honmei_sei": 本命星名, "tsukimei_sei": 月命星名} or None (エラー時)
        """
        try:
            # --- 年の計算 (立春前に生まれた場合は前年扱い) ---
            # 簡易的に2月3日生まれまでを前年扱いとする (厳密には年により変動)
            calc_year = birth_year
            if birth_month == 1 or (birth_month == 2 and birth_day <= 3):
                calc_year -= 1

            # --- 本命星の計算 ---
            honmei_sei = self._get_honmei_sei(calc_year)
            if honmei_sei == "不明":
                raise ValueError("本命星の計算に失敗しました。")

            # 本命星の番号を取得 (月命星計算用)
            honmei_sei_num = self.kyusei_dict_rev.get(honmei_sei)
            if honmei_sei_num is None:
                raise ValueError("本命星番号の取得に失敗しました。")

            # --- 月命星の計算 ---
            month_number = self._get_month_number(birth_month, birth_day)
            if month_number == 0:
                raise ValueError("月番号の計算に失敗しました。")

            # 月命星を計算
            tsukimei_sei = self._get_tsukimei_sei(honmei_sei_num, month_number)
            if tsukimei_sei == "不明":
                raise ValueError("月命星の計算に失敗しました。")

            # 結果を辞書で返す
            return {
                "honmei_sei": honmei_sei,
                "tsukimei_sei": tsukimei_sei
            }

        except Exception as e:
            print(f"九星気学計算エラー: {e}")
            return None

    def get_fortune(self, birth_date):
        """
        九星気学による運勢を取得する
        
        Args:
            birth_date (str): YYYY-MM-DD形式の生年月日
            
        Returns:
            dict: 運勢情報
        """
        try:
            # 生年月日を分解
            date_parts = birth_date.split('-')
            if len(date_parts) != 3:
                raise ValueError("生年月日の形式が正しくありません。YYYY-MM-DD形式で入力してください。")
            
            birth_year = int(date_parts[0])
            birth_month = int(date_parts[1])
            birth_day = int(date_parts[2])
            
            # 九星気学の計算
            result = self.calculate_kyusei(birth_year, birth_month, birth_day)
            if result is None:
                raise ValueError("九星気学の計算に失敗しました。")
            
            honmei_sei = result['honmei_sei']
            tsukimei_sei = result['tsukimei_sei']
            
            # 運勢の説明を生成
            fortune = f"{honmei_sei}のあなたは、{tsukimei_sei}の影響を受けています。"
            
            # 本命星と月命星の組み合わせに基づく運勢の詳細
            description = self._get_fortune_description(honmei_sei, tsukimei_sei)
            
            return {
                "number": self.kyusei_dict_rev.get(honmei_sei, 0),
                "type": honmei_sei,
                "tsukimei": tsukimei_sei,
                "fortune": fortune,
                "description": description
            }
            
        except Exception as e:
            print(f"運勢計算エラー: {e}")
            return {
                "number": 0,
                "type": "不明",
                "tsukimei": "不明",
                "fortune": "運勢の計算に失敗しました。",
                "description": str(e)
            }
    
    def _get_fortune_description(self, honmei_sei, tsukimei_sei):
        """
        本命星と月命星の組み合わせに基づく運勢の詳細を生成する
        
        Args:
            honmei_sei (str): 本命星の名前
            tsukimei_sei (str): 月命星の名前
            
        Returns:
            str: 運勢の詳細な説明
        """
        # 簡易的な運勢説明（実際のアプリケーションではより詳細なデータベースを使用）
        descriptions = {
            "一白水星": "知性と直感力に優れ、新しいアイデアを生み出す力があります。",
            "二黒土星": "堅実で忍耐強く、着実に目標を達成する力があります。",
            "三碧木星": "活発で行動力があり、リーダーシップを発揮します。",
            "四緑木星": "調和とバランスを重視し、周囲との関係を良好に保ちます。",
            "五黄土星": "中心的な存在で、周囲をまとめる力があります。",
            "六白金星": "正義感が強く、公平な判断力を持っています。",
            "七赤金星": "情熱的で魅力的、人を惹きつける力があります。",
            "八白土星": "安定感があり、着実に物事を進める力があります。",
            "九紫火星": "創造性と情熱に富み、新しい可能性を切り開きます。"
        }
        
        honmei_desc = descriptions.get(honmei_sei, "特徴的な性格を持っています。")
        tsukimei_desc = descriptions.get(tsukimei_sei, "現在の環境に適応しています。")
        
        return f"あなたの本命星は{honmei_sei}で、{honmei_desc} 月命星は{tsukimei_sei}で、{tsukimei_desc} この組み合わせから、あなたは現在、新しい挑戦に適した時期にあります。"

def calculate_kyusei(year, month, day):
    """九星気学の計算を行う関数"""
    try:
        # 生年月日から九星を計算
        honmei = calculate_honmei(year, month, day)
        gatsumei = calculate_gatsumei(year, month, day)
        
        return {
            'honmei_sei': honmei,
            'tsukimei_sei': gatsumei
        }
    except Exception as e:
        print(f"九星気学の計算でエラーが発生しました: {str(e)}")
        return None

def calculate_honmei(year, month, day):
    """
    本命星を計算する関数
    
    Args:
        year (int): 生まれた年（西暦）
        month (int): 生まれた月（1-12）
        day (int): 生まれた日（1-31）
        
    Returns:
        str: 本命星の名前
    """
    # 2月4日より前の生まれは前年扱い
    if month == 1 or (month == 2 and day < 4):
        year -= 1
    
    # 九星の計算
    kyusei_numbers = {
        1: "一白水星",
        2: "二黒土星",
        3: "三碧木星",
        4: "四緑木星",
        5: "五黄土星",
        6: "六白金星",
        7: "七赤金星",
        8: "八白土星",
        9: "九紫火星"
    }
    
    remainder = (11 - (year % 9)) % 9
    if remainder == 0:
        remainder = 9
    
    return kyusei_numbers.get(remainder, "不明")

def calculate_gatsumei(year, month, day):
    """
    月命星を計算する関数
    
    Args:
        year (int): 生まれた年（西暦）
        month (int): 生まれた月（1-12）
        day (int): 生まれた日（1-31）
        
    Returns:
        str: 月命星の名前
    """
    # 本命星を取得
    honmei = calculate_honmei(year, month, day)
    
    # 本命星の番号を取得
    kyusei_dict_rev = {
        "一白水星": 1, "二黒土星": 2, "三碧木星": 3, "四緑木星": 4,
        "五黄土星": 5, "六白金星": 6, "七赤金星": 7, "八白土星": 8,
        "九紫火星": 9
    }
    honmei_num = kyusei_dict_rev.get(honmei)
    
    # 月番号を取得（節入り日で変わる）
    def get_month_number(month, day):
        if (month == 1 and day < 6) or (month == 12 and day >= 7): return 11
        elif (month == 2 and day < 4) or (month == 1 and day >= 6): return 12
        elif (month == 3 and day < 6) or (month == 2 and day >= 4): return 1
        elif (month == 4 and day < 5) or (month == 3 and day >= 6): return 2
        elif (month == 5 and day < 6) or (month == 4 and day >= 5): return 3
        elif (month == 6 and day < 6) or (month == 5 and day >= 6): return 4
        elif (month == 7 and day < 8) or (month == 6 and day >= 6): return 5
        elif (month == 8 and day < 8) or (month == 7 and day >= 8): return 6
        elif (month == 9 and day < 8) or (month == 8 and day >= 8): return 7
        elif (month == 10 and day < 9) or (month == 9 and day >= 8): return 8
        elif (month == 11 and day < 8) or (month == 10 and day >= 9): return 9
        elif (month == 12 and day < 7) or (month == 11 and day >= 8): return 10
        return 0
    
    month_number = get_month_number(month, day)
    
    # 本命星のグループに基づく基準値
    if honmei_num in [1, 4, 7]:  # 水・木・金グループ
        base_num = 8  # 2月は八白
    elif honmei_num in [2, 5, 8]:  # 土グループ
        base_num = 2  # 2月は二黒
    elif honmei_num in [3, 6, 9]:  # 木・金・火グループ
        base_num = 5  # 2月は五黄
    else:
        return "不明"
    
    # 月命星の計算
    kyusei_numbers = {
        1: "一白水星", 2: "二黒土星", 3: "三碧木星",
        4: "四緑木星", 5: "五黄土星", 6: "六白金星",
        7: "七赤金星", 8: "八白土星", 9: "九紫火星"
    }
    
    gatsumei_num = (base_num - (month_number - 1)) % 9
    if gatsumei_num <= 0:
        gatsumei_num += 9
    
    return kyusei_numbers.get(gatsumei_num, "不明") 