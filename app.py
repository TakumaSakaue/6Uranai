"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import pytz
import os
import traceback

# --- 占いモジュールをインポート ---
try:
    from modules.kyusei import KyuseiFortune, calculate_kyusei, calculate_honmei, calculate_gatsumei
    from modules.western import calculate_astrology, _initialize_skyfield, _loader as skyfield_loader
    from modules.doubutsu import calculate_animal_fortune
    from modules.inyou import calculate_inyou_gogyo
    from modules.shichuu import calculate_shichuu
except ImportError as e:
    print(f"FATAL: 占いモジュールのインポートに失敗しました: {e}")
    print("kyusei.py, western.py, doubutsu.py, inyou.py, shichuu.py が同じディレクトリに存在するか確認してください。")
    exit(1)

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)

# --- Skyfieldの初期化 ---
SKYFIELD_DATA_DIR = os.path.join(os.path.dirname(__file__), "skyfield-data")
os.makedirs(SKYFIELD_DATA_DIR, exist_ok=True)
print(f"Skyfieldデータディレクトリ: {SKYFIELD_DATA_DIR}")
try:
    _initialize_skyfield(SKYFIELD_DATA_DIR)
except Exception as e:
    print(f"FATAL: Skyfieldの初期化に失敗しました: {e}")
    traceback.print_exc()

# --- APIエンドポイント: /predict (占い実行) ---
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        
        if not all([year, month, day]):
            return jsonify({'error': '生年月日が正しく指定されていません'}), 400
            
        # 四柱推命の計算
        shichuu_result = calculate_shichuu(year, month, day)
        print(f"四柱推命の計算結果: {shichuu_result}")
        
        # 九星気学の計算
        print("九星気学の計算を開始します...")
        try:
            honmei = calculate_honmei(year, month, day)
            gatsumei = calculate_gatsumei(year, month, day)
            kyusei_result = {
                "honmei": honmei,
                "gatsumei": gatsumei
            }
            print(f"九星気学の計算結果: {kyusei_result}")
        except Exception as e:
            print(f"九星気学の計算でエラーが発生しました: {str(e)}")
            kyusei_result = {"error": "九星気学の計算に失敗しました"}
        
        # どうぶつ占いの計算
        animal_result = calculate_animal_fortune(year, month, day)
        print(f"どうぶつ占いの計算結果: {animal_result}")
        
        # 西洋占星術の計算
        western_result = calculate_astrology(year, month, day)
        print(f"西洋占星術の計算結果: {western_result}")
        
        # 陰陽五行の計算
        inyou_result = calculate_inyou_gogyo(year, month, day)
        print(f"陰陽五行の計算結果: {inyou_result}")
        
        return jsonify({
            'shichuu': shichuu_result,
            'kyusei': kyusei_result,
            'animal': animal_result,
            'western': western_result,
            'inyou': inyou_result
        })
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- ルートエンドポイント: / (HTML配信) ---
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"エラー: {str(e)}")
        return jsonify({"error": "フロントエンドファイルが見つかりません。"}), 404

# Vercel Serverless環境用のエントリーポイント
app.debug = False 