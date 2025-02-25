# tools/chat_glm4.py
from langchain.llms.base import LLM
from zhipuai import ZhipuAI
from langchain_core.messages.ai import AIMessage
from typing import List, Optional
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取 OpenAI API 密钥 & 自定义 API 地址
zhipuai_api_key = os.getenv("zhipuai_api_key")  # 默认值为 "EMPTY"

class ChatGLM4(LLM):
    history: List[dict] = []  # 记录对话历史
    client: Optional[ZhipuAI] = None  # 智谱 AI 客户端

    def __init__(self):
        super().__init__()
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatGLM4"

    def invoke(self, prompt, config={}, history=None):
        if history is None:
            history = []
        if isinstance(prompt, list):  # 兼容 LangChain 消息格式
            prompt = prompt[-1].content  # 取最新的用户输入
        history.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="glm-4",
            messages=history
        )
        result = response.choices[0].message.content
        return AIMessage(content=result)

    def _call(self, prompt, config, history=None):
        return self.invoke(prompt, history)

    def stream(self, prompt, config={}, history=None):
        if history is None:
            history = []
        if isinstance(prompt, list):
            prompt = prompt[-1].content  # 取最新的用户输入

        history.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=history,
            stream=True
        )
        for chunk in response:
            yield chunk.choices[0].delta.content
# 在ChatGLM4类中添加
    async def async_generate(self, user_text: str):
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": user_text}],
            stream=False
        )
        return response.choices[0].message.content