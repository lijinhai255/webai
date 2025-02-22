# main.py
import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis
import uvicorn
from LLM.chat_glm4 import ChatGLM4

app = FastAPI(title="智能对话服务", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 精确匹配前端地址
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 必须包含OPTIONS方法[2,5](@ref)
    allow_headers=["*"],
    expose_headers=["*"]
)
# 增强会话管理（文献3）
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_pool = redis.ConnectionPool(
            host='localhost', port=6379, db=0,
            decode_responses=True, max_connections=20
        )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def get_redis(self):
        return redis.Redis(connection_pool=self.redis_pool)

# 增强消息格式兼容性（文献4）
class ChatRequest(BaseModel):
    user_input: str
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    message_type: Optional[str] = "text"  # text/voice

manager = ConnectionManager()
chat_glm = ChatGLM4()

@app.websocket("/ws/chat/glm4")
async def chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    redis_client = manager.get_redis()
    try:
        while True:
            data = await websocket.receive_json()
            session_id = data.get("session_id") or str(uuid4())
            
            # 语音消息处理（文献5）
            if data.get("message_type") == "voice":
                await handle_voice_message(data, session_id, redis_client)
                continue

            # 保存对话记录
            redis_client.rpush(
                f"session:{session_id}",
                json.dumps({
                    "role": "user",
                    "content": data["user_input"],
                    "timestamp": datetime.now().isoformat()
                })
            )

            # 流式响应
            response_buffer = []
            async for chunk in chat_glm.async_stream(data["user_input"]):
                response_buffer.append(chunk)
                await websocket.send_text(json.dumps({
                    "content": "".join(response_buffer),
                    "type": "text_stream",
                    "session_id": session_id
                }))

            # 保存AI响应
            redis_client.rpush(
                f"session:{session_id}",
                json.dumps({
                    "role": "assistant",
                    "content": "".join(response_buffer),
                    "timestamp": datetime.now().isoformat()
                })
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"处理失败: {str(e)}"
        })
@app.get("/dtai")
async def dtai_endpoint(user_text: str):  # 接收查询参数
    # 调用ChatGLM4模型处理
    response = await chat_glm.async_generate(user_text)
    return {
        "type": "content",
        "val": response,
        "data": {
            "actions": []  # 根据实际业务补充
        }
    }
@app.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    """获取完整对话历史（文献2）"""
    redis_client = manager.get_redis()
    return [
        json.loads(msg) 
        for msg in redis_client.lrange(f"session:{session_id}", 0, -1)
    ]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=300
    )