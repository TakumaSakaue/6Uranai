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
def get_module_path(module_name):
    """モジュールの絶対パスを取得"""
    try:
        # 現在のファイルの絶対パスを取得
        current_file = pathlib.Path(__file__).resolve()
        logger.debug(f"現在のファイルパス: {current_file}")
        
        # modulesディレクトリのパスを構築
        modules_dir = current_file.parent / 'modules'
        logger.debug(f"モジュールディレクトリパス: {modules_dir}")
        
        # モジュールファイルのパスを構築
        module_path = modules_dir / f'{module_name}.py'
        logger.debug(f"モジュールファイルパス: {module_path}")
        
        return module_path
    except Exception as e:
        logger.error(f"モジュールパスの取得に失敗: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def import_module(module_name):
    """モジュールを動的にインポート"""
    try:
        logger.info(f"{module_name}モジュールのインポートを開始")
        
        # モジュールのパスを取得
        module_path = get_module_path(module_name)
        if module_path is None:
            logger.error(f"モジュールパスの取得に失敗: {module_name}")
            return None
            
        if not module_path.exists():
            logger.error(f"モジュールファイルが見つかりません: {module_path}")
            # ディレクトリ内のファイル一覧を表示
            try:
                logger.debug(f"ディレクトリ内容: {list(module_path.parent.glob('*'))}")
            except Exception as e:
                logger.error(f"ディレクトリ内容の取得に失敗: {str(e)}")
            return None
            
        # モジュールをインポート
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None:
            logger.error(f"モジュール仕様の取得に失敗: {module_name}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"モジュールの実行に失敗: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        
        logger.info(f"{module_name}モジュールのインポートが完了")
        return module
    except Exception as e:
        logger.error(f"{module_name}モジュールのインポートでエラー: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def load_modules():
    """必要なモジュールをすべてロード"""
    try:
        logger.info("モジュールのインポートを開始")
        
        # 現在の環境情報をログ出力
        logger.debug(f"現在の作業ディレクトリ: {os.getcwd()}")
        logger.debug(f"PYTHONPATH: {sys.path}")
        logger.debug(f"環境変数: {dict(os.environ)}")
        
        # 各モジュールをインポート
        modules = {}
        for module_name in ['kyusei', 'doubutsu', 'inyou', 'shichuu']:
            module = import_module(module_name)
            if module is None:
                logger.error(f"{module_name}モジュールのインポートに失敗")
                return None, None, None, None, None
            modules[module_name] = module
        
        # 必要な関数を取得
        functions = {
            'calculate_honmei': getattr(modules['kyusei'], 'calculate_honmei', None),
            'calculate_gatsumei': getattr(modules['kyusei'], 'calculate_gatsumei', None),
            'calculate_animal_fortune': getattr(modules['doubutsu'], 'calculate_animal_fortune', None),
            'calculate_inyou_gogyo': getattr(modules['inyou'], 'calculate_inyou_gogyo', None),
            'calculate_shichuu': getattr(modules['shichuu'], 'calculate_shichuu', None)
        }
        
        # 必要な関数が全て存在するか確認
        missing_functions = [name for name, func in functions.items() if func is None]
        if missing_functions:
            logger.error(f"以下の関数が見つかりません: {missing_functions}")
            return None, None, None, None, None
            
        logger.info("全モジュールが正常にロードされました")
        return (
            functions['calculate_honmei'],
            functions['calculate_gatsumei'],
            functions['calculate_animal_fortune'],
            functions['calculate_inyou_gogyo'],
            functions['calculate_shichuu']
        )
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
app.debug = True 