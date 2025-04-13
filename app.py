"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
import os
import traceback

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)

# --- 占いモジュールをインポート ---
try:
    from modules.kyusei import calculate_honmei, calculate_gatsumei
    from modules.doubutsu import calculate_animal_fortune
    from modules.inyou import calculate_inyou_gogyo
    from modules.shichuu import calculate_shichuu
except ImportError as e:
    print(f"FATAL: 占いモジュールのインポートに失敗しました: {e}")
    print("必要なモジュールが存在するか確認してください。")

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
        
        # 九星気学の計算
        try:
            honmei = calculate_honmei(year, month, day)
            gatsumei = calculate_gatsumei(year, month, day)
            kyusei_result = {
                "honmei": honmei,
                "gatsumei": gatsumei
            }
        except Exception as e:
            kyusei_result = {"error": "九星気学の計算に失敗しました"}
        
        # どうぶつ占いの計算
        animal_result = calculate_animal_fortune(year, month, day)
        
        # 陰陽五行の計算
        inyou_result = calculate_inyou_gogyo(year, month, day)
        
        return jsonify({
            'shichuu': shichuu_result,
            'kyusei': kyusei_result,
            'animal': animal_result,
            'inyou': inyou_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ルートエンドポイント: / (HTML配信) ---
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({"error": "フロントエンドファイルが見つかりません。"}), 404

# Vercel Serverless環境用のエントリーポイント
app.debug = False 