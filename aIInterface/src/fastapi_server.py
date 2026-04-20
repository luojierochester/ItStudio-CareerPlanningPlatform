from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Literal
import json
import os
import asyncio
from pathlib import Path
from openai import AsyncOpenAI
import logging
import PyPDF2
from docx import Document

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chat Service")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 配置部分 =====
# 外部大模型API配置（用于测试阶段）
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY", "your-api-key-here")
EXTERNAL_BASE_URL = os.getenv("EXTERNAL_BASE_URL", "https://api.siliconflow.cn/v1")
EXTERNAL_MODEL = os.getenv("EXTERNAL_MODEL", "deepseek-ai/DeepSeek-V3")

# 本地llama.cpp/Ollama配置（用于生产阶段）
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "qwen2")

# 当前使用的模型类型：external 或 local
MODEL_TYPE = os.getenv("MODEL_TYPE", "external")

# 文件存储路径（与后端保持一致）
FILE_STORAGE_PATH = Path(os.getenv("FILE_STORAGE_PATH", "/root/temp/saveFileTest"))

# Redis 配置（用于读取缓存的简历文本）
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# 路径配置
BASE_DIR = Path(__file__).parent.parent
PROMPT_DIR = BASE_DIR / "prompt"
PROFILE_DIR = BASE_DIR / "profiles"

# 确保目录存在
PROMPT_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

# ===== 初始化客户端 =====
def get_client() -> AsyncOpenAI:
    """根据配置返回对应的OpenAI客户端"""
    if MODEL_TYPE == "local":
        return AsyncOpenAI(
            api_key="ollama",  # llama.cpp/Ollama不需要真实key
            base_url=LOCAL_BASE_URL,
            http_client=None  # 避免 proxies 参数问题
        )
    else:
        return AsyncOpenAI(
            api_key=EXTERNAL_API_KEY,
            base_url=EXTERNAL_BASE_URL,
            http_client=None  # 避免 proxies 参数问题
        )

def get_model_name() -> str:
    """返回当前使用的模型名称"""
    return LOCAL_MODEL if MODEL_TYPE == "local" else EXTERNAL_MODEL

# ===== 数据库工具函数 =====
def get_resume_from_redis(user_id: str) -> Optional[str]:
    """从 Redis 读取用户的简历文本缓存（与后端保持一致）"""
    try:
        import redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        cache_key = f"resume:text:{user_id}"
        resume_text = r.get(cache_key)
        return resume_text
    except Exception as e:
        logger.error(f"Redis 读取失败: {e}")
        return None

def get_resume_from_file(user_id: str) -> Optional[str]:
    """从磁盘读取用户的简历文件（备用方案）"""
    try:
        # 后端文件命名格式: resume_{accountId}.{extension}
        for ext in ['pdf', 'docx']:
            file_path = FILE_STORAGE_PATH / f"resume_{user_id}.{ext}"
            if file_path.exists():
                if ext == 'pdf':
                    return read_pdf(file_path)
                elif ext == 'docx':
                    return read_docx(file_path)
        return None
    except Exception as e:
        logger.error(f"文件读取失败: {e}")
        return None

def read_pdf(file_path: Path) -> str:
    """读取PDF文件内容"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        logger.error(f"读取PDF文件失败: {e}")
        return ""

def read_docx(file_path: Path) -> str:
    """读取DOCX文件内容"""
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        logger.error(f"读取DOCX文件失败: {e}")
        return ""

# ===== 数据模型 =====
class ChatSession(BaseModel):
    uuid: str
    has_file: bool = False
    user_id: Optional[str] = None
    profile_path: Optional[str] = None

# 会话管理
active_sessions: Dict[str, ChatSession] = {}

# ===== 工具函数 =====
def load_prompt(agent_type: Literal["Agent01", "Agent02"]) -> str:
    """加载对应的提示词文件"""
    prompt_file = PROMPT_DIR / f"{agent_type}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    else:
        logger.warning(f"提示词文件 {prompt_file} 不存在，使用默认提示词")
        if agent_type == "Agent01":
            return """你是一个专业的职业规划AI助手。用户已上传简历文件，请基于简历内容提供个性化的职业规划建议。
你需要：
1. 分析用户的技能、经验和背景
2. 提供针对性的职业发展建议
3. 推荐合适的职位和发展方向
4. 帮助用户完善简历和提升竞争力"""
        else:
            return """你是一个专业的职业规划AI助手。用户选择直接对话，请通过提问引导用户：
1. 了解用户的教育背景、专业和年级
2. 了解用户的技能和项目经验
3. 了解用户的职业兴趣和目标
4. 基于收集的信息提供职业规划建议
请循序渐进地提问，不要一次问太多问题。"""

def load_user_profile(user_id: str) -> Optional[Dict]:
    """加载用户画像文件"""
    profile_file = PROFILE_DIR / f"{user_id}_profile.json"
    if profile_file.exists():
        try:
            return json.loads(profile_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"加载用户画像失败: {e}")
            return None
    return None

def save_user_profile(user_id: str, profile_data: Dict):
    """保存/更新用户画像文件"""
    profile_file = PROFILE_DIR / f"{user_id}_profile.json"
    try:
        profile_file.write_text(json.dumps(profile_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"用户画像已保存: {profile_file}")
    except Exception as e:
        logger.error(f"保存用户画像失败: {e}")

async def update_profile_with_ai(user_id: str, conversation_history: list):
    """
    使用AI分析对话历史，更新用户画像
    """
    try:
        client = get_client()
        model = get_model_name()

        # 构建提取用户信息的提示词
        extraction_prompt = """请分析以下对话，提取用户的关键信息，以JSON格式返回：
{
  "name": "姓名（如果提到）",
  "education": "教育背景",
  "major": "专业",
  "grade": "年级",
  "skills": ["技能1", "技能2"],
  "projects": ["项目1", "项目2"],
  "interests": ["兴趣1", "兴趣2"],
  "career_goals": "职业目标",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["待提升1", "待提升2"]
}

只返回JSON，不要其他内容。如果某项信息未提及，使用null或空数组。

对话历史：
"""
        # 添加最近的对话历史（最多10轮）
        recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        for msg in recent_history:
            extraction_prompt += f"\n{msg['role']}: {msg['content']}"

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.3
        )

        ai_output = response.choices[0].message.content.strip()

        # 尝试解析JSON
        try:
            # 移除可能的markdown代码块标记
            if ai_output.startswith("```"):
                ai_output = ai_output.split("```")[1]
                if ai_output.startswith("json"):
                    ai_output = ai_output[4:]

            profile_updates = json.loads(ai_output)

            # 加载现有画像
            existing_profile = load_user_profile(user_id) or {}

            # 合并更新（只更新非空值）
            for key, value in profile_updates.items():
                if value and value != "null":
                    if isinstance(value, list) and len(value) > 0:
                        # 对于列表类型，合并去重
                        existing_list = existing_profile.get(key, [])
                        if isinstance(existing_list, list):
                            existing_profile[key] = list(set(existing_list + value))
                        else:
                            existing_profile[key] = value
                    elif isinstance(value, str) and value.strip():
                        existing_profile[key] = value

            # 添加更新时间戳
            from datetime import datetime
            existing_profile["last_updated"] = datetime.now().isoformat()

            # 保存更新后的画像
            save_user_profile(user_id, existing_profile)
            logger.info(f"用户画像已更新: {user_id}")

        except json.JSONDecodeError as e:
            logger.error(f"解析AI返回的JSON失败: {e}, 原始输出: {ai_output}")

    except Exception as e:
        logger.error(f"更新用户画像时出错: {e}")

# ===== API端点 =====
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "model_type": MODEL_TYPE,
        "model_name": get_model_name()
    }

@app.get("/api/v1/ai-chat/new-chat")
async def new_chat():
    """创建新的聊天会话，返回 UUID（适配后端接口）"""
    import uuid as uuid_lib
    new_uuid = str(uuid_lib.uuid4())
    logger.info(f"创建新会话: {new_uuid}")
    return {
        "code": 200,
        "message": "success",
        "data": new_uuid
    }

@app.websocket("/ws/v1/ai-chat")
async def websocket_chat(
    websocket: WebSocket,
    uuid: str = Query(...),
    has_file: bool = Query(False),
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket聊天端点（完全适配后端接口）

    参数:
    - uuid: 会话唯一标识（由后端生成）
    - has_file: 是否上传了文件（true=使用Agent01，false=使用Agent02）
    - user_id: 用户ID（用于加载/保存用户画像）
    """
    await websocket.accept()
    logger.info(f"WebSocket连接建立: uuid={uuid}, has_file={has_file}, user_id={user_id}")

    # 创建会话
    session = ChatSession(uuid=uuid, has_file=has_file, user_id=user_id)
    active_sessions[uuid] = session

    # 选择对应的提示词
    agent_type = "Agent01" if has_file else "Agent02"
    system_prompt = load_prompt(agent_type)

    # 如果用户上传了简历，读取简历内容
    resume_content = None
    if has_file and user_id:
        try:
            # 优先从 Redis 读取（与后端保持一致）
            resume_content = get_resume_from_redis(user_id)

            # 如果 Redis 没有，尝试从文件读取
            if not resume_content:
                resume_content = get_resume_from_file(user_id)

            if resume_content:
                logger.info(f"成功读取用户 {user_id} 的简历，长度: {len(resume_content)}")
                # 将简历内容添加到系统提示词
                system_prompt += f"\n\n用户简历内容：\n{resume_content}"
            else:
                logger.warning(f"用户 {user_id} 没有找到简历")
        except Exception as e:
            logger.error(f"读取简历时出错: {e}")

    # 加载用户画像（如果存在）
    user_profile = None
    if user_id:
        user_profile = load_user_profile(user_id)
        if user_profile:
            # 将用户画像添加到系统提示词中
            profile_text = f"\n\n用户画像：\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}"
            system_prompt += profile_text

    # 对话历史
    conversation_history = [{"role": "system", "content": system_prompt}]

    # 发送欢迎消息
    welcome_msg = "你好！我是你的职业规划AI助手。" + (
        "我看到你已经上传了简历，让我来帮你分析一下。" if has_file
        else "让我们一起探索你的职业发展方向吧！首先，能告诉我你目前的教育背景吗？"
    )
    await websocket.send_text(welcome_msg)

    try:
        client = get_client()
        model = get_model_name()

        while True:
            # 接收用户消息
            user_message = await websocket.receive_text()

            # 处理心跳
            if user_message == '{"type":"ping"}':
                await websocket.send_text("pong")
                continue

            logger.info(f"收到用户消息: {user_message[:100]}...")

            # 添加到对话历史
            conversation_history.append({"role": "user", "content": user_message})

            # 调用大模型（流式输出）
            try:
                stream = await client.chat.completions.create(
                    model=model,
                    messages=conversation_history,
                    temperature=0.7,
                    stream=True
                )

                full_response = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 流式发送给前端
                        await websocket.send_text(content)

                # 添加完整回复到对话历史
                conversation_history.append({"role": "assistant", "content": full_response})

                # 每轮对话后更新用户画像
                if user_id and len(conversation_history) >= 4:  # 至少有2轮对话后才更新
                    asyncio.create_task(update_profile_with_ai(user_id, conversation_history))

            except Exception as e:
                logger.error(f"调用大模型失败: {e}")
                error_msg = f"抱歉，服务暂时不可用: {str(e)}"
                await websocket.send_text(error_msg)

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: uuid={uuid}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        # 清理会话
        if uuid in active_sessions:
            del active_sessions[uuid]

# ===== 辅助HTTP端点（用于测试和管理）=====
@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """获取用户画像"""
    profile = load_user_profile(user_id)
    if profile:
        return {"status": "success", "data": profile}
    else:
        raise HTTPException(status_code=404, detail="用户画像不存在")

@app.post("/api/profile/{user_id}")
async def update_profile(user_id: str, profile_data: Dict):
    """手动更新用户画像"""
    save_user_profile(user_id, profile_data)
    return {"status": "success", "message": "用户画像已更新"}

@app.get("/api/sessions")
async def list_sessions():
    """列出当前活跃的会话"""
    return {
        "status": "success",
        "data": {
            "count": len(active_sessions),
            "sessions": [
                {"uuid": s.uuid, "has_file": s.has_file, "user_id": s.user_id}
                for s in active_sessions.values()
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
