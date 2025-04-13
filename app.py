"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import os
import traceback
import logging
import sys
from werkzeug.middleware.proxy_fix import ProxyFix

# --- ロギングの設定 ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# --- 占いモジュールをインポート ---
def load_modules():
    try:
        logger.info("モジュールのインポートを開始")
        from modules.kyusei import calculate_honmei, calculate_gatsumei
        logger.debug("九星気学モジュールをロード完了")
        
        from modules.doubutsu import calculate_animal_fortune
        logger.debug("動物占いモジュールをロード完了")
        
        from modules.inyou import calculate_inyou_gogyo
        logger.debug("陰陽五行モジュールをロード完了")
        
        from modules.shichuu import calculate_shichuu
        logger.debug("四柱推命モジュールをロード完了")
        
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
        request_data = request.get_json()
        logger.info(f"受信したリクエストデータ: {request_data}")
        
        if not request_data:
            logger.error("JSONデータが見つかりません")
            return jsonify({'error': 'JSONデータが見つかりません'}), 400

        # 入力データの検証
        try:
            year = int(request_data.get('year', 0))
            month = int(request_data.get('month', 0))
            day = int(request_data.get('day', 0))
            
            if not all([year, month, day]):
                raise ValueError("生年月日が正しく指定されていません")
                
            logger.info(f"処理する生年月日: {year}年{month}月{day}日")
            
        except (ValueError, TypeError) as e:
            logger.error(f"入力データの変換エラー: {e}")
            return jsonify({'error': f'入力データが不正です: {str(e)}'}), 400

        # モジュールのロード
        calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu = load_modules()
        if None in (calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu):
            logger.error("必要なモジュールのロードに失敗しました")
            return jsonify({'error': 'サーバー内部エラー: モジュールのロードに失敗'}), 500

        response_data = {}
        
        # 四柱推命の計算
        try:
            shichuu_result = calculate_shichuu(year, month, day)
            logger.debug(f"四柱推命の計算結果: {shichuu_result}")
            response_data['shichuu'] = shichuu_result
        except Exception as e:
            logger.error(f"四柱推命の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            response_data['shichuu'] = {"error": f"四柱推命の計算に失敗: {str(e)}"}
        
        # 九星気学の計算
        try:
            honmei = calculate_honmei(year, month, day)
            gatsumei = calculate_gatsumei(year, month, day)
            kyusei_result = {
                "honmei": honmei,
                "gatsumei": gatsumei
            }
            logger.debug(f"九星気学の計算結果: {kyusei_result}")
            response_data['kyusei'] = kyusei_result
        except Exception as e:
            logger.error(f"九星気学の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            response_data['kyusei'] = {"error": f"九星気学の計算に失敗: {str(e)}"}
        
        # どうぶつ占いの計算
        try:
            animal_result = calculate_animal_fortune(year, month, day)
            logger.debug(f"どうぶつ占いの計算結果: {animal_result}")
            response_data['animal'] = animal_result
        except Exception as e:
            logger.error(f"どうぶつ占いの計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            response_data['animal'] = {"error": f"どうぶつ占いの計算に失敗: {str(e)}"}
        
        # 陰陽五行の計算
        try:
            inyou_result = calculate_inyou_gogyo(year, month, day)
            logger.debug(f"陰陽五行の計算結果: {inyou_result}")
            response_data['inyou'] = inyou_result
        except Exception as e:
            logger.error(f"陰陽五行の計算でエラー: {str(e)}")
            logger.error(traceback.format_exc())
            response_data['inyou'] = {"error": f"陰陽五行の計算に失敗: {str(e)}"}

        logger.info("全ての計算が完了しました")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'サーバー内部エラー: {str(e)}'}), 500

# --- ルートエンドポイント: / (HTML配信) ---
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"フロントエンドファイルの読み込みでエラー: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "フロントエンドファイルが見つかりません"}), 404

# Vercel Serverless環境用のエントリーポイント
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(host='127.0.0.1', port=port, debug=True) 