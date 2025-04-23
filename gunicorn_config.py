import multiprocessing
import os

# ワーカー数の設定（CPU数に基づく）
workers = multiprocessing.cpu_count() * 2 + 1

# ワーカークラスの設定
worker_class = 'gevent'

# タイムアウト設定
timeout = 60

# プリロードの有効化
preload_app = True

# ワーカーの最大リクエスト数
max_requests = 1000
max_requests_jitter = 50

# バッファサイズの設定
buffer_size = 32768

# ログ設定
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# プロセス名の設定
proc_name = 'uranai_app'

# デーモンモードの設定
daemon = False

# バインドアドレスの設定
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# グレースフルシャットダウンの設定
graceful_timeout = 30

# キープアライブの設定
keepalive = 5

# バックログの設定
backlog = 2048

# ワーカーの接続タイムアウト
worker_connections = 1000

# ワーカーの一時停止時間
worker_tmp_dir = '/dev/shm'

# ワーカーの最大同時リクエスト数
worker_class_args = {
    'worker_connections': 1000,
    'keepalive': 5,
    'timeout': 30
} 