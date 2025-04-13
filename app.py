"""
占いAPIサーバー
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
import pytz # western.py 内でも使われるが、明示的にインポートしておくとわかりやすい場合がある
import os
import traceback # エラー詳細ログ用
import argparse # コマンドライン引数用

# --- 占いモジュールをインポート ---
# 各ファイルが存在し、指定された関数が定義されている必要があります
try:
    from modules.kyusei import KyuseiFortune, calculate_kyusei, calculate_honmei, calculate_gatsumei
    from modules.western import calculate_astrology, _initialize_skyfield, _loader as skyfield_loader # 初期化とクローズ用にloaderもインポート
    from modules.doubutsu import calculate_animal_fortune
    from modules.inyou import calculate_inyou_gogyo
    from modules.shichuu import calculate_shichuu
except ImportError as e:
    print(f"FATAL: 占いモジュールのインポートに失敗しました: {e}")
    print("kyusei.py, western.py, doubutsu.py, inyou.py, shichuu.py が同じディレクトリに存在するか確認してください。")
    exit(1) # 起動時エラーなので終了

# --- Flaskアプリケーションの作成 ---
app = Flask(__name__)

# --- Skyfieldの初期化 ---
# 環境変数 SKYFIELD_DATA_DIR があればそれを使用、なければ 'skyfield-data' を使用
SKYFIELD_DATA_DIR = os.environ.get("SKYFIELD_DATA_DIR", "skyfield-data")
# データディレクトリが存在しない場合は作成
os.makedirs(SKYFIELD_DATA_DIR, exist_ok=True)
print(f"Skyfieldデータディレクトリ: {SKYFIELD_DATA_DIR}")
try:
    # western.py内の初期化関数を呼び出す
    _initialize_skyfield(SKYFIELD_DATA_DIR)
except Exception as e:
    print(f"FATAL: Skyfieldの初期化に失敗しました: {e}")
    traceback.print_exc()
    # 本番環境ではここで起動を停止するか、エラー状態を示すフラグを立てる
    exit(1)

# --- ヘルパー関数: 日付検証 ---
def validate_birthdate(date_str):
    """
    YYYY-MM-DD形式の日付文字列を検証し、datetimeオブジェクトを返す。
    不正な形式や未来の日付の場合はNoneを返す。
    """
    if not date_str:
        return None
    try:
        birth_dt = datetime.strptime(date_str, "%Y-%m-%d")
        # 簡単な未来日付チェック (当日を含む場合は <= にする)
        # タイムゾーンを考慮しない単純比較
        if birth_dt.date() > datetime.now().date():
            print(f"検証エラー: 未来の日付です - {date_str}")
            return None
        # ここで年の範囲チェックなども追加可能 (例: 1900年以降など)
        # if birth_dt.year < 1900:
        #     print(f"検証エラー: 年が範囲外です - {birth_dt.year}")
        #     return None
        return birth_dt
    except ValueError:
        print(f"検証エラー: 日付フォーマットが不正です - {date_str}")
        return None

# --- APIエンドポイント: /predict (占い実行) ---
@app.route('/predict', methods=['POST'])
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
    """
    ルートパスにアクセスされた際に index.html を返す。
    index.html は templates ディレクトリにある想定。
    """
    try:
        return render_template('index.html')
    except FileNotFoundError:
        print("エラー: index.html が見つかりません。")
        return jsonify({"error": "フロントエンドファイルが見つかりません。"}), 404

# --- アプリケーション終了時の処理 (Skyfield Loader クローズ) ---
@app.teardown_appcontext
def close_skyfield_loader(exception=None):
    """
    リクエスト処理後やアプリ終了時にSkyfieldのLoaderを閉じる。
    """
    global skyfield_loader # western.py からインポートした Loader インスタンス
    if skyfield_loader:
        try:
            skyfield_loader.close()
            print("Skyfield Loader closed.")
        except Exception as e:
            print(f"Skyfield Loaderのクローズ中にエラー: {e}")

# --- Flaskアプリの実行 ---
if __name__ == '__main__':
    print("Skyfield initialized.")
    print("サーバーを起動します: http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=True)
    # 本番環境では Gunicorn や uWSGI などのWSGIサーバーを使用し、debug=False にする 