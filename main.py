from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import date, datetime
import logging
from modules.doubutsu import calculate_animal_fortune
from modules.kyusei import calculate_kyusei
from modules.western import calculate_astrology
from modules.shichuu import calculate_shichuu

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="static"), name="static")

class BirthDate(BaseModel):
    year: int
    month: int
    day: int

class BirthDateString(BaseModel):
    birthdate: str

@app.get("/")
async def root():
    return FileResponse("templates/index.html")

@app.post("/predict")
async def get_fortune(request: Request):
    try:
        # リクエストボディをログに出力
        body = await request.json()
        logger.info(f"リクエストボディ: {body}")
        
        # リクエストの形式に応じて処理を分岐
        if 'birthdate' in body:
            # YYYY-MM-DD形式の場合
            try:
                birth_date = datetime.strptime(body['birthdate'], '%Y-%m-%d')
                year = birth_date.year
                month = birth_date.month
                day = birth_date.day
            except ValueError:
                raise HTTPException(status_code=422, detail="日付の形式が不正です。YYYY-MM-DD形式で入力してください。")
        elif 'year' in body and 'month' in body and 'day' in body:
            # 年、月、日が個別に指定されている場合
            year = body['year']
            month = body['month']
            day = body['day']
        else:
            raise HTTPException(status_code=422, detail="リクエストボディに 'birthdate' または 'year', 'month', 'day' が必要です。")
        
        # 各占いの計算を実行
        kyusei_result = calculate_kyusei(year, month, day)
        western_result = calculate_astrology(year, month, day)
        animal_result = calculate_animal_fortune(year, month, day)
        shichuu_result = calculate_shichuu(year, month, day)
        
        # 結果をログに出力
        result = {
            "kyusei_kigaku": kyusei_result,
            "western_astrology": western_result,
            "doubutsu_uranai": animal_result,
            "shichuu": shichuu_result
        }
        logger.info(f"計算結果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 