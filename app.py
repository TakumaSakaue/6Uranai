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
import importlib.util
import pathlib

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

# --- モジュールのインポート処理 ---
def import_module(module_name):
    try:
        logger.info(f"{module_name}モジュールのインポートを開始")
        
        # モジュールのパスを構築
        module_path = pathlib.Path(__file__).parent / 'modules' / f'{module_name}.py'
        
        if not module_path.exists():
            logger.error(f"モジュールファイルが見つかりません: {module_path}")
            return None
            
        # モジュールをインポート
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            logger.error(f"モジュール仕様の取得に失敗: {module_name}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        logger.info(f"{module_name}モジュールのインポートが完了")
        return module
    except Exception as e:
        logger.error(f"{module_name}モジュールのインポートでエラー: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def load_modules():
    try:
        logger.info("モジュールのインポートを開始")
        
        # 各モジュールをインポート
        kyusei = import_module('kyusei')
        doubutsu = import_module('doubutsu')
        inyou = import_module('inyou')
        shichuu = import_module('shichuu')
        
        if None in (kyusei, doubutsu, inyou, shichuu):
            logger.error("一部のモジュールのインポートに失敗")
            return None, None, None, None, None
        
        # 必要な関数を取得
        calculate_honmei = getattr(kyusei, 'calculate_honmei', None)
        calculate_gatsumei = getattr(kyusei, 'calculate_gatsumei', None)
        calculate_animal_fortune = getattr(doubutsu, 'calculate_animal_fortune', None)
        calculate_inyou_gogyo = getattr(inyou, 'calculate_inyou_gogyo', None)
        calculate_shichuu = getattr(shichuu, 'calculate_shichuu', None)
        
        if None in (calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu):
            logger.error("必要な関数が見つかりません")
            return None, None, None, None, None
            
        logger.info("全モジュールが正常にロードされました")
        return calculate_honmei, calculate_gatsumei, calculate_animal_fortune, calculate_inyou_gogyo, calculate_shichuu
    except Exception as e:
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