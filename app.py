"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import os
import traceback
import logging
from werkzeug.serving import WSGIRequestHandler
import signal
import sys

# --- ロギングの設定 ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)

# タイムアウトとバッファサイズの設定
WSGIRequestHandler.protocol_version = "HTTP/1.1"
WSGIRequestHandler.timeout = 60

# グレースフルシャットダウンのハンドラー
def signal_handler(sig, frame):
    logger.info('シャットダウンシグナルを受信しました...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# --- 占いモジュールをインポート ---
def load_modules():
    try:
        from modules.kyusei import calculate_honmei, calculate_gatsumei
        from modules.doubutsu import calculate_animal_fortune
        from modules.inyou import calculate_inyou_gogyo
        from modules.shichuu import calculate_shichuu
        from modules.sukuyo import calculate_sukuyo
        from modules.western import calculate_western_astrology
        logger.info("全モジュールが正常にロードされました")
        return calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu, calculate_sukuyo, calculate_western_astrology
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗: {e}")
        logger.error(traceback.format_exc())
        return None, None, None, None, None, None, None

# --- APIエンドポイント: /api/predict (占い実行) ---
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "データがありません"}), 400

        year = int(data.get('year', 0))
        month = int(data.get('month', 0))
        day = int(data.get('day', 0))

        if not all([year, month, day]):
            return jsonify({"error": "生年月日が正しく指定されていません"}), 400

        # 四柱推命の計算
        shichuu_result = calculate_shichuu(year, month, day)
        
        # どうぶつ占いの計算
        animal_result = calculate_animal_fortune(year, month, day)

        return jsonify({
            "shichuu": shichuu_result,
            "animal": {"animal_character": animal_result}
        })

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- ルートエンドポイント: / (HTML配信) ---
@app.route('/')
def index():
    return render_template('index.html')

# ローカル環境用のエントリーポイント
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False) 