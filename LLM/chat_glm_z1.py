from langchain.llms.base import LLM
from zhipuai import ZhipuAI
from langchain_core.messages.ai import AIMessage
from typing import List, Optional
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取 API 密钥
zhipuai_api_key = os.getenv("zhipuai_api_key")

class ChatGLMZ1(LLM):
    history: List[dict] = []  # 记录对话历史
    client: Optional[ZhipuAI] = None  # 智谱 AI 客户端

    def __init__(self):
        super().__init__()
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatGLMZ1"

    def invoke(self, prompt, config={}, history=None):
        if history is None:
            history = []
        if isinstance(prompt, list):  # 兼容 LangChain 消息格式
            prompt = prompt[-1].content  # 取最新的用户输入
        history.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="glm-z1-flash",  # 使用免费的推理模型
            messages=history
        )
        result = response.choices[0].message.content
        return AIMessage(content=result)

    def _call(self, prompt, config={}, history=None):
        return self.invoke(prompt, history)

    def stream(self, prompt, config={}, history=None):
        if history is None:
            history = []
        if isinstance(prompt, list):
            prompt = prompt[-1].content  # 取最新的用户输入

        history.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model="glm-z1-flash",  # 使用免费的推理模型
            messages=history,
            stream=True
        )
        for chunk in response:
            yield chunk.choices[0].delta.content