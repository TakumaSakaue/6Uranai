"""
陰陽五行の計算モジュール
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

# 十干（天干）リスト
jikkan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 十二支（地支）リスト
junishi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十干と五行・陰陽の対応表
jikkan_to_gogyo_inyo = {
    '甲': {'gogyo': '木', 'inyo': '陽'},
    '乙': {'gogyo': '木', 'inyo': '陰'},
    '丙': {'gogyo': '火', 'inyo': '陽'},
    '丁': {'gogyo': '火', 'inyo': '陰'},
    '戊': {'gogyo': '土', 'inyo': '陽'},
    '己': {'gogyo': '土', 'inyo': '陰'},
    '庚': {'gogyo': '金', 'inyo': '陽'},
    '辛': {'gogyo': '金', 'inyo': '陰'},
    '壬': {'gogyo': '水', 'inyo': '陽'},
    '癸': {'gogyo': '水', 'inyo': '陰'},
}

# 十二支と五行の対応表
junishi_to_gogyo = {
    '子': '水',
    '丑': '土',
    '寅': '木',
    '卯': '木',
    '辰': '土',
    '巳': '火',
    '午': '火',
    '未': '土',
    '申': '金',
    '酉': '金',
    '戌': '土',
    '亥': '水',
}

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

# 天干と地支を分割する
def split_pillar(pillar):
    return pillar[0], pillar[1]

# 天干から五行と陰陽を取得
def get_gogyo_inyo_from_jikkan(jikkan):
    return jikkan_to_gogyo_inyo.get(jikkan, {})

# 地支から五行を取得
def get_gogyo_from_junishi(junishi):
    return junishi_to_gogyo.get(junishi, '')

# 四柱から陰陽五行の詳細を計算
def calculate_gogyo_inyo(year_pillar, month_pillar, day_pillar):
    # 各柱を天干と地支に分割
    year_jikkan, year_junishi = split_pillar(year_pillar)
    month_jikkan, month_junishi = split_pillar(month_pillar)
    day_jikkan, day_junishi = split_pillar(day_pillar)
    
    # 各天干の五行と陰陽を取得
    year_jikkan_info = get_gogyo_inyo_from_jikkan(year_jikkan)
    month_jikkan_info = get_gogyo_inyo_from_jikkan(month_jikkan)
    day_jikkan_info = get_gogyo_inyo_from_jikkan(day_jikkan)
    
    # 各地支の五行を取得
    year_junishi_gogyo = get_gogyo_from_junishi(year_junishi)
    month_junishi_gogyo = get_gogyo_from_junishi(month_junishi)
    day_junishi_gogyo = get_gogyo_from_junishi(day_junishi)
    
    # 本質を表す日干の陰陽五行
    essence_gogyo_inyo = {
        'gogyo': day_jikkan_info.get('gogyo', ''),
        'inyo': day_jikkan_info.get('inyo', '')
    }
    
    # 五行バランスの計算
    gogyo_counts = {
        '木': 0,
        '火': 0,
        '土': 0,
        '金': 0,
        '水': 0
    }
    
    # 天干の五行をカウント
    for info in [year_jikkan_info, month_jikkan_info, day_jikkan_info]:
        gogyo = info.get('gogyo', '')
        if gogyo:
            gogyo_counts[gogyo] += 1
    
    # 地支の五行をカウント
    for gogyo in [year_junishi_gogyo, month_junishi_gogyo, day_junishi_gogyo]:
        if gogyo:
            gogyo_counts[gogyo] += 1
    
    # 最も多い五行と最も少ない五行を特定
    max_gogyo = max(gogyo_counts.items(), key=lambda x: x[1])
    min_gogyo = min(gogyo_counts.items(), key=lambda x: x[1])
    
    return {
        'year_pillar': {
            'pillar': year_pillar,
            'jikkan': year_jikkan,
            'junishi': year_junishi,
            'jikkan_gogyo': year_jikkan_info.get('gogyo', ''),
            'jikkan_inyo': year_jikkan_info.get('inyo', ''),
            'junishi_gogyo': year_junishi_gogyo
        },
        'month_pillar': {
            'pillar': month_pillar,
            'jikkan': month_jikkan,
            'junishi': month_junishi,
            'jikkan_gogyo': month_jikkan_info.get('gogyo', ''),
            'jikkan_inyo': month_jikkan_info.get('inyo', ''),
            'junishi_gogyo': month_junishi_gogyo
        },
        'day_pillar': {
            'pillar': day_pillar,
            'jikkan': day_jikkan,
            'junishi': day_junishi,
            'jikkan_gogyo': day_jikkan_info.get('gogyo', ''),
            'jikkan_inyo': day_jikkan_info.get('inyo', ''),
            'junishi_gogyo': day_junishi_gogyo
        },
        'essence': essence_gogyo_inyo,
        'gogyo_balance': {
            'counts': gogyo_counts,
            'strongest': max_gogyo[0],
            'strongest_count': max_gogyo[1],
            'weakest': min_gogyo[0],
            'weakest_count': min_gogyo[1]
        }
    }

# 年・月・日柱をまとめて返す
def get_pillars(year, month, day):
    year_pillar = get_year_pillar(year, month, day)
    month_pillar = get_month_pillar(year, month, day)
    day_pillar = get_day_pillar(year, month, day)
    
    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar
    }

# 生年月日から四柱と陰陽五行の詳細を取得
def get_four_pillars_analysis(year, month, day):
    pillars = get_pillars(year, month, day)
    year_pillar = pillars["year_pillar"]
    month_pillar = pillars["month_pillar"]
    day_pillar = pillars["day_pillar"]
    
    # 陰陽五行の詳細を計算
    analysis = calculate_gogyo_inyo(year_pillar, month_pillar, day_pillar)
    
    return {
        "pillars": pillars,
        "analysis": analysis
    }

# 陰陽五行の計算結果を返す
def calculate_inyou_gogyo(year, month, day):
    """
    生年月日から陰陽五行を計算する関数
    """
    try:
        # 日柱を取得
        day_pillar = get_day_pillar(year, month, day)
        
        # 日柱の天干を取得
        day_jikkan = day_pillar[0]
        
        # 天干から五行と陰陽を取得
        jikkan_info = jikkan_to_gogyo_inyo.get(day_jikkan, {})
        gogyo = jikkan_info.get('gogyo', '')
        inyo = jikkan_info.get('inyo', '')
        
        print(f"日柱: {day_pillar}, 日干: {day_jikkan}, 五行: {gogyo}, 陰陽: {inyo}")
        
        if not gogyo or not inyo:
            print("五行または陰陽の取得に失敗しました")
            return None
            
        return {
            "gogyo": gogyo,
            "inyo": inyo
        }
        
    except Exception as e:
        print(f"陰陽五行の計算でエラーが発生: {e}")
        traceback.print_exc()
        return None

# テスト実行用
if __name__ == '__main__':
    # 例: 1983年7月5日
    birth_year = 1983
    birth_month = 7
    birth_day = 5
    
    results = get_four_pillars_analysis(birth_year, birth_month, birth_day)
    
    print(f"生年月日: {birth_year}-{birth_month:02d}-{birth_day:02d}")
    print("\n【四柱】")
    print(f"年柱: {results['pillars']['year_pillar']}")
    print(f"月柱: {results['pillars']['month_pillar']}")
    print(f"日柱: {results['pillars']['day_pillar']}")
    
    print("\n【詳細分析】")
    analysis = results['analysis']
    
    print("\n年柱:")
    year_info = analysis['year_pillar']
    print(f"  天干: {year_info['jikkan']} ({year_info['jikkan_gogyo']}の{year_info['jikkan_inyo']})")
    print(f"  地支: {year_info['junishi']} ({year_info['junishi_gogyo']})")
    
    print("\n月柱:")
    month_info = analysis['month_pillar']
    print(f"  天干: {month_info['jikkan']} ({month_info['jikkan_gogyo']}の{month_info['jikkan_inyo']})")
    print(f"  地支: {month_info['junishi']} ({month_info['junishi_gogyo']})")
    
    print("\n日柱:")
    day_info = analysis['day_pillar']
    print(f"  天干: {day_info['jikkan']} ({day_info['jikkan_gogyo']}の{day_info['jikkan_inyo']})")
    print(f"  地支: {day_info['junishi']} ({day_info['junishi_gogyo']})")
    
    print("\n【日干：本質の陰陽五行】")
    print(f"{analysis['essence']['gogyo']}の{analysis['essence']['inyo']}")
    
    print("\n【五行バランス】")
    balance = analysis['gogyo_balance']
    for gogyo, count in balance['counts'].items():
        print(f"{gogyo}: {count}回")
    print(f"\n最も強い五行: {balance['strongest']} ({balance['strongest_count']}回)")
    print(f"最も弱い五行: {balance['weakest']} ({balance['weakest_count']}回)") 