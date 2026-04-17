@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ======================================================
echo   大学生简历-岗位推荐系统 Demo
echo ======================================================
echo.

:: ==================== 配置区 ====================
set "MODEL_PATH=./model"
set "DB_URI=sqlite:///jobs.db"
set "JOBS_CSV=data/jobs.csv"
set "FAISS_INDEX=./models/job_faiss.index"
set "LGB_MODEL=./models/lgb/lgb_model.joblib"
set "FEATURE_CSV=./data/features_examples.csv"
set "RECALL_K=50"
set "TOPN=10"

set "RESUME_TEXT=我熟悉Python和PyTorch，有推荐系统课程项目经历，曾参加蓝桥杯竞赛，有实习经历，持有英语六级证书"
:: ======================================================

:: Step 0：检查文件
if not exist "%FEATURE_CSV%" (
    echo [错误] 未找到特征词典文件：%FEATURE_CSV%
    pause
    exit /b 1
)
echo [Step 0] 特征词典已就绪：%FEATURE_CSV%

if not exist "%JOBS_CSV%" (
    echo [错误] 未找到岗位数据文件：%JOBS_CSV%
    pause
    exit /b 1
)
echo [Step 0] 岗位数据已就绪：%JOBS_CSV%
echo.

:: Step 1：编码入库
echo ======================================================
echo [Step 1] 正在将岗位数据编码并写入数据库...
echo ======================================================
python src/encode_jobs_db.py ^
    --jobs_csv "%JOBS_CSV%" ^
    --model_name_or_path "%MODEL_PATH%" ^
    --db_uri "%DB_URI%" ^
    --faiss_index_path "%FAISS_INDEX%"
echo [Step 1] 完成！
echo.

:: Step 2：推理推荐
echo ======================================================
echo [Step 2] 正在执行岗位推荐...
echo ======================================================
echo 简历文本：%RESUME_TEXT%
echo.

if exist "%LGB_MODEL%" (
    echo [Info] 检测到 LightGBM 模型，使用精排模式
    python src/inference_pipeline_db.py ^
        --model_path "%MODEL_PATH%" ^
        --db_uri "%DB_URI%" ^
        --resume_text "%RESUME_TEXT%" ^
        --recall_k "%RECALL_K%" ^
        --topn "%TOPN%" ^
        --lgb_model "%LGB_MODEL%" ^
        --faiss_index_path "%FAISS_INDEX%"
) else (
    echo [Info] 未检测到 LightGBM 模型，使用规则打分模式
    python src/inference_pipeline_db.py ^
        --model_path "%MODEL_PATH%" ^
        --db_uri "%DB_URI%" ^
        --resume_text "%RESUME_TEXT%" ^
        --recall_k "%RECALL_K%" ^
        --topn "%TOPN%" ^
        --faiss_index_path "%FAISS_INDEX%"
)

echo.
echo [Step 2] 推荐完成！
echo.

:: 提示
echo ======================================================
echo [可选] 启动 API 服务
echo ======================================================
echo 如需启动 FastAPI 服务，请执行：
echo.
echo     python src/api.py
echo.
echo 访问：
echo     http://localhost:8001/health
echo     http://localhost:8001/docs
echo ======================================================
echo  Demo 完成
echo ======================================================

pause