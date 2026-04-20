"""
AI聊天服务主入口
运行此文件启动FastAPI服务器
"""
import uvicorn
import os
from pathlib import Path

# 设置环境变量（可根据需要修改）
os.environ.setdefault("MODEL_TYPE", "external")  # 或 "local"
os.environ.setdefault("EXTERNAL_API_KEY", "sk-mvzmmntpjvhiihcotelnytqqvltecoiqvydmywqquqcxxqfm")
os.environ.setdefault("EXTERNAL_BASE_URL", "https://api.siliconflow.cn/v1/")
os.environ.setdefault("EXTERNAL_MODEL", "deepseek-ai/DeepSeek-V3.2")
os.environ.setdefault("PORT", "8002")

def main():
    """启动FastAPI服务器"""
    port = int(os.getenv("PORT", "8002"))

    print("=" * 60)
    print("AI职业规划聊天服务")
    print("=" * 60)
    print(f"服务地址: http://localhost:{port}")
    print(f"健康检查: http://localhost:{port}/health")
    print(f"API文档: http://localhost:{port}/docs")
    print(f"模型类型: {os.getenv('MODEL_TYPE')}")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")

    # 启动服务器
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )

if __name__ == "__main__":
    main()
