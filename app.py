"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import os
import traceback
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

# --- ロギングの設定 ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# --- 占いモジュールをインポート ---
def load_modules():
    try:
        from modules.kyusei import calculate_honmei, calculate_gatsumei
        from modules.doubutsu import calculate_animal_fortune
        from modules.inyou import calculate_inyou_gogyo
        from modules.shichuu import calculate_shichuu
        logger.info("全モジュールが正常にロードされました")
        return calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗: {e}")
        logger.error(traceback.format_exc())
        return None, None, None, None, None

# --- APIエンドポイント: /api/predict (占い実行) ---
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # リクエストデータのログ
        logger.debug(f"受信したリクエストデータ: {request.get_json()}")
        
        # モジュールの動的ロード
        calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu = load_modules()
        if None in (calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu):
            logger.error("モジュールのロードに失敗しました")
            return jsonify({'error': 'モジュールの読み込みに失敗しました'}), 500

        data = request.get_json()
        if not data:
            logger.error("JSONデータが見つかりません")
            return jsonify({'error': 'JSONデータが見つかりません'}), 400

        year = int(data.get('year', 0))
        month = int(data.get('month', 0))
        day = int(data.get('day', 0))
        
        logger.debug(f"入力データ: year={year}, month={month}, day={day}")
        
        if not all([year, month, day]):
            logger.error(f"不正な入力データ: year={year}, month={month}, day={day}")
            return jsonify({'error': '生年月日が正しく指定されていません'}), 400
            
        # 四柱推命の計算
        try:
            shichuu_result = calculate_shichuu(year, month, day)
            logger.debug(f"四柱推命の計算結果: {shichuu_result}")
        except Exception as e:
            logger.error(f"四柱推命の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            shichuu_result = {"error": "四柱推命の計算に失敗しました"}
        
        # 九星気学の計算
        try:
            honmei = calculate_honmei(year, month, day)
            gatsumei = calculate_gatsumei(year, month, day)
            kyusei_result = {
                "honmei": honmei,
                "gatsumei": gatsumei
            }
            logger.debug(f"九星気学の計算結果: {kyusei_result}")
        except Exception as e:
            logger.error(f"九星気学の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            kyusei_result = {"error": "九星気学の計算に失敗しました"}
        
        # どうぶつ占いの計算
        try:
            animal_result = calculate_animal_fortune(year, month, day)
            logger.debug(f"どうぶつ占いの計算結果: {animal_result}")
        except Exception as e:
            logger.error(f"どうぶつ占いの計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            animal_result = {"error": "どうぶつ占いの計算に失敗しました"}
        
        # 陰陽五行の計算
        try:
            inyou_result = calculate_inyou_gogyo(year, month, day)
            logger.debug(f"陰陽五行の計算結果: {inyou_result}")
        except Exception as e:
            logger.error(f"陰陽五行の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            inyou_result = {"error": "陰陽五行の計算に失敗しました"}
        
        response_data = {
            'shichuu': shichuu_result,
            'kyusei': kyusei_result,
            'animal': animal_result,
            'inyou': inyou_result
        }
        logger.info(f"レスポンスデータ: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'予期せぬエラーが発生しました: {str(e)}'}), 500

# --- ルートエンドポイント: / (HTML配信) ---
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"フロントエンドファイルの読み込みでエラー: {str(e)}")
        return jsonify({"error": "フロントエンドファイルが見つかりません"}), 404

# Vercel Serverless環境用のエントリーポイント
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(host='127.0.0.1', port=port, debug=True) 