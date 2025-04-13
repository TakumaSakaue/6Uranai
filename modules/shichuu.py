"""
四柱推命の計算モジュール
"""
from datetime import datetime, timedelta, timezone
from skyfield.api import load, utc
import traceback

# 干支リスト（60干支）
eto_list = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

# 天干と地支のリスト
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 陽干と陰干の定義
YANG_GAN = ["甲", "丙", "戊", "庚", "壬"]  # 陽干（奇数）
YIN_GAN = ["乙", "丁", "己", "辛", "癸"]   # 陰干（偶数）

# 年干支（60干支）を返す（1984年＝甲子を基準）
def get_eto_from_year(year):
    base_year = 1984
    index = (year - base_year) % 60
    return eto_list[index]

# 立春（黄道経度315°）のJST時刻をSkyfieldで計算
def get_setsubun_datetime(year):
    ts = load.timescale()
    eph = load('de421.bsp')
    sun = eph['sun']
    earth = eph['earth']
    t = ts.utc(datetime(year, 2, 1, 0, 0, tzinfo=utc))
    end_t = ts.utc(datetime(year, 2, 5, 0, 0, tzinfo=utc))
    delta = timedelta(minutes=1)
    while t.utc_datetime() < end_t.utc_datetime():
        obs = earth.at(t).observe(sun).apparent()
        lon = obs.ecliptic_latlon()[1].degrees
        if lon >= 315.0:
            return t.utc_datetime() + timedelta(hours=9)
        t = ts.utc((t.utc_datetime() + delta).replace(tzinfo=utc))
    return None

# 年柱を返す（立春補正あり）
def get_year_pillar(year, month, day, hour=12, minute=0):
    JST = timezone(timedelta(hours=9))
    birth = datetime(year, month, day, hour, minute, tzinfo=JST)
    setsubun = get_setsubun_datetime(year)
    if setsubun and birth < setsubun:
        year -= 1
    return get_eto_from_year(year)

# 月の節入り（12節気）のJST時刻をSkyfieldで計算
def get_month_start_dates(year):
    approx_dates = {
        315.0: (2, 4), 345.0: (3, 6), 15.0: (4, 5), 45.0: (5, 6),
        75.0: (6, 6), 105.0: (7, 7), 135.0: (8, 8), 165.0: (9, 8),
        195.0: (10, 8), 225.0: (11, 7), 255.0: (12, 7), 285.0: (1, 6)
    }
    ts = load.timescale()
    eph = load('de421.bsp')
    sun = eph['sun']
    earth = eph['earth']
    results = []
    for angle, (m, d) in approx_dates.items():
        target_year = year if angle != 285.0 else year + 1
        t_start = datetime(target_year, m, d - 1, tzinfo=utc)
        t_end = datetime(target_year, m, d + 1, tzinfo=utc)
        t = ts.utc(t_start)
        end_t = ts.utc(t_end)
        delta = timedelta(minutes=1)
        while t.utc_datetime() < end_t.utc_datetime():
            obs = earth.at(t).observe(sun).apparent()
            lon = obs.ecliptic_latlon()[1].degrees
            if lon >= angle:
                jst = t.utc_datetime() + timedelta(hours=9)
                results.append((angle, jst))
                break
            t = ts.utc((t.utc_datetime() + delta).replace(tzinfo=utc))
    results.sort(key=lambda x: x[1])
    return results

# 月番号を取得（寅＝1、丑＝12）
def get_month_index(year, month, day, hour=12, minute=0):
    JST = timezone(timedelta(hours=9))
    birth = datetime(year, month, day, hour, minute, tzinfo=JST)
    month_starts = get_month_start_dates(year)
    for i in range(len(month_starts)):
        _, start_time = month_starts[i]
        if i == len(month_starts) - 1:
            if birth >= start_time:
                return i + 1
        else:
            _, next_time = month_starts[i + 1]
            if start_time <= birth < next_time:
                return i + 1
    return 12

# 月柱の干支を取得
def get_month_pillar(year, month, day, hour=12, minute=0):
    year_eto = get_year_pillar(year, month, day, hour, minute)
    year_kan = year_eto[0]
    month_index = get_month_index(year, month, day, hour, minute)
    year_to_tora_kan = {
        '甲': '丙', '乙': '戊', '丙': '庚', '丁': '壬', '戊': '甲',
        '己': '丙', '庚': '戊', '辛': '庚', '壬': '壬', '癸': '甲'
    }
    tora_kan = year_to_tora_kan[year_kan]
    jikkan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    junishi = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']
    tora_index = jikkan.index(tora_kan)
    kan_index = (tora_index + month_index - 1) % 10
    return f"{jikkan[kan_index]}{junishi[month_index - 1]}"

# 日柱（1984年1月31日を甲子として計算）
def get_day_pillar(year, month, day):
    JST = timezone(timedelta(hours=9))
    birth = datetime(year, month, day, 0, 0, tzinfo=JST)
    base = datetime(1984, 1, 31, 0, 0, tzinfo=JST)
    delta_days = (birth - base).days
    index = delta_days % 60
    return eto_list[index]

# 各天干に対する十二運の地支順序マッピング
# 陽干（甲、丙、戊、庚、壬）の十二運マッピング
YANG_GAN_OPERATIONS = {
    "甲": {
        "亥": "長生", "子": "沐浴", "丑": "冠帯", "寅": "建禄", "卯": "帝旺", "辰": "衰",
        "巳": "病", "午": "死", "未": "墓", "申": "絶", "酉": "胎", "戌": "養"
    },
    "丙": {
        "寅": "長生", "卯": "沐浴", "辰": "冠帯", "巳": "建禄", "午": "帝旺", "未": "衰",
        "申": "病", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養"
    },
    "戊": {
        "寅": "長生", "卯": "沐浴", "辰": "冠帯", "巳": "建禄", "午": "帝旺", "未": "衰",
        "申": "病", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養"
    },
    "庚": {
        "巳": "長生", "午": "沐浴", "未": "冠帯", "申": "建禄", "酉": "帝旺", "戌": "衰",
        "亥": "病", "子": "死", "丑": "墓", "寅": "絶", "卯": "胎", "辰": "養"
    },
    "壬": {
        "申": "長生", "酉": "沐浴", "戌": "冠帯", "亥": "建禄", "子": "帝旺", "丑": "衰",
        "寅": "病", "卯": "死", "辰": "墓", "巳": "絶", "午": "胎", "未": "養"
    }
}

# 陰干（乙、丁、己、辛、癸）の十二運マッピング
YIN_GAN_OPERATIONS = {
    "乙": {
        "午": "長生", "巳": "沐浴", "辰": "冠帯", "卯": "建禄", "寅": "帝旺", "丑": "衰",
        "子": "病", "亥": "死", "戌": "墓", "酉": "絶", "申": "胎", "未": "養"
    },
    "丁": {
        "酉": "長生", "申": "沐浴", "未": "冠帯", "午": "建禄", "巳": "帝旺", "辰": "衰",
        "卯": "病", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養"
    },
    "己": {
        "酉": "長生", "申": "沐浴", "未": "冠帯", "午": "建禄", "巳": "帝旺", "辰": "衰",
        "卯": "病", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養"
    },
    "辛": {
        "子": "長生", "亥": "沐浴", "戌": "冠帯", "酉": "建禄", "申": "帝旺", "未": "衰",
        "午": "病", "巳": "死", "辰": "墓", "卯": "絶", "寅": "胎", "丑": "養"
    },
    "癸": {
        "卯": "長生", "寅": "沐浴", "丑": "冠帯", "子": "建禄", "亥": "帝旺", "戌": "衰",
        "酉": "病", "申": "死", "未": "墓", "午": "絶", "巳": "胎", "辰": "養"
    }
}

# 通変星（宿命星）のマッピング
DESTINY_STAR_MAPPING = {
    "甲": {
        "甲": "比肩", "乙": "劫財", "丙": "食神", "丁": "傷官", "戊": "偏財", "己": "正財",
        "庚": "偏官", "辛": "正官", "壬": "偏印", "癸": "印綬"
    },
    "乙": {
        "甲": "劫財", "乙": "比肩", "丙": "傷官", "丁": "食神", "戊": "正財", "己": "偏財",
        "庚": "正官", "辛": "偏官", "壬": "印綬", "癸": "偏印"
    },
    "丙": {
        "甲": "偏印", "乙": "印綬", "丙": "比肩", "丁": "劫財", "戊": "食神", "己": "傷官",
        "庚": "偏財", "辛": "正財", "壬": "偏官", "癸": "正官"
    },
    "丁": {
        "甲": "印綬", "乙": "偏印", "丙": "劫財", "丁": "比肩", "戊": "傷官", "己": "食神",
        "庚": "正財", "辛": "偏財", "壬": "正官", "癸": "偏官"
    },
    "戊": {
        "甲": "偏官", "乙": "正官", "丙": "偏印", "丁": "印綬", "戊": "比肩", "己": "劫財",
        "庚": "食神", "辛": "傷官", "壬": "偏財", "癸": "正財"
    },
    "己": {
        "甲": "正官", "乙": "偏官", "丙": "印綬", "丁": "偏印", "戊": "劫財", "己": "比肩",
        "庚": "傷官", "辛": "食神", "壬": "正財", "癸": "偏財"
    },
    "庚": {
        "甲": "偏財", "乙": "正財", "丙": "偏官", "丁": "正官", "戊": "偏印", "己": "印綬",
        "庚": "比肩", "辛": "劫財", "壬": "食神", "癸": "傷官"
    },
    "辛": {
        "甲": "正財", "乙": "偏財", "丙": "正官", "丁": "偏官", "戊": "印綬", "己": "偏印",
        "庚": "劫財", "辛": "比肩", "壬": "傷官", "癸": "食神"
    },
    "壬": {
        "甲": "食神", "乙": "傷官", "丙": "偏財", "丁": "正財", "戊": "偏官", "己": "正官",
        "庚": "偏印", "辛": "印綬", "壬": "比肩", "癸": "劫財"
    },
    "癸": {
        "甲": "傷官", "乙": "食神", "丙": "正財", "丁": "偏財", "戊": "正官", "己": "偏官",
        "庚": "印綬", "辛": "偏印", "壬": "劫財", "癸": "比肩"
    }
}

# 日柱天干を取得（日柱の干部分）
def get_day_tian_gan(day_pillar):
    return day_pillar[0]

# 日柱十二運を取得
def get_day_twelve_operation(day_pillar):
    day_gan = day_pillar[0]  # 日柱の天干
    day_zhi = day_pillar[1]  # 日柱の地支
    
    # 日干が陽干か陰干かによって十二運マッピングを選択
    if day_gan in YANG_GAN:
        return YANG_GAN_OPERATIONS[day_gan][day_zhi]
    else:
        return YIN_GAN_OPERATIONS[day_gan][day_zhi]

# 地支の蔵干マッピング（各地支に隠れている天干）
# 主気、中気、余気の順に格納
DI_ZHI_HIDDEN_GAN = {
    "子": ["癸", None, None],  # 子には「癸」が蔵されている
    "丑": ["己", "癸", "辛"],  # 丑には「己」「癸」「辛」が蔵されている
    "寅": ["甲", "丙", "戊"],  # 寅には「甲」「丙」「戊」が蔵されている
    "卯": ["乙", None, None],  # 卯には「乙」が蔵されている
    "辰": ["戊", "乙", "癸"],  # 辰には「戊」「乙」「癸」が蔵されている
    "巳": ["丙", "庚", "戊"],  # 巳には「丙」「庚」「戊」が蔵されている
    "午": ["丁", "己", None],  # 午には「丁」「己」が蔵されている
    "未": ["己", "丁", "乙"],  # 未には「己」「丁」「乙」が蔵されている
    "申": ["庚", "壬", "戊"],  # 申には「庚」「壬」「戊」が蔵されている
    "酉": ["辛", None, None],  # 酉には「辛」が蔵されている
    "戌": ["戊", "辛", "丁"],  # 戌には「戊」「辛」「丁」が蔵されている
    "亥": ["壬", "甲", None]   # 亥には「壬」「甲」が蔵されている
}

# 月干の蔵干宿命星を取得（月支の蔵干を考慮）
def get_month_gan_destiny_star(day_pillar, month_pillar):
    day_gan = day_pillar[0]  # 日柱の天干
    month_zhi = month_pillar[1]  # 月柱の地支
    
    # 月支の蔵干を取得（主気のみ使用）
    month_hidden_gan = DI_ZHI_HIDDEN_GAN[month_zhi][0]
    
    # 日干と月支蔵干の組み合わせで宿命星を判定
    return DESTINY_STAR_MAPPING[day_gan][month_hidden_gan]

# 年・月・日柱と重要な要素をまとめて返す
def get_full_sizhu_info(year, month, day):
    # 基本の四柱を取得
    year_pillar = get_year_pillar(year, month, day)
    month_pillar = get_month_pillar(year, month, day)
    day_pillar = get_day_pillar(year, month, day)
    
    # 重要な要素を計算
    day_tian_gan = get_day_tian_gan(day_pillar)
    day_twelve_operation = get_day_twelve_operation(day_pillar)
    month_gan_destiny_star = get_month_gan_destiny_star(day_pillar, month_pillar)
    
    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "day_tian_gan": day_tian_gan,
        "day_twelve_operation": day_twelve_operation,
        "month_gan_destiny_star": month_gan_destiny_star
    }

def calculate_shichuu(year, month, day):
    """
    四柱推命の計算を行う関数
    """
    try:
        # 四柱推命の情報を取得
        sizhu_info = get_full_sizhu_info(year, month, day)
        
        # 結果を返す
        return {
            "day_tian_gan": sizhu_info["day_tian_gan"],
            "day_twelve_operation": sizhu_info["day_twelve_operation"],
            "month_gan_destiny_star": sizhu_info["month_gan_destiny_star"]
        }
    except Exception as e:
        print(f"四柱推命の計算でエラーが発生しました: {e}")
        return None

# テスト実行
if __name__ == '__main__':
    # 1983年7月5日の四柱推命を計算
    result = calculate_shichuu(1983, 7, 5)
    print("四柱推命の計算結果:")
    print(result) 