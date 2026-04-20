import os
import sys

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# 设置工作目录为 algorithm 根目录（确保模型路径正确）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from inference_pipeline_db import RecommendationEngine

app = FastAPI(title="职位推荐算法接口")

from feature_engineering_db import load_feature_keywords
load_feature_keywords()

engine = None

class RecommendRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, description="简历文本")
    recall_k: int = Field(300, ge=1, le=500, description="召回候选数")
    topn: int = Field(10, ge=1, le=50, description="最终返回数量")

@app.on_event("startup")
def startup():
    global engine
    engine = RecommendationEngine(
        model_path="./model",
        db_uri="sqlite:///jobs.db",
        lgb_model_path="./models/lgb/lgb_model.joblib",
        faiss_index_path="./models/job_faiss.index"
    )
    engine.load()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    try:
        result = engine.recommend(
            resume_text=req.resume_text,
            recall_k=req.recall_k,
            topn=req.topn
        )
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"recommendation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)