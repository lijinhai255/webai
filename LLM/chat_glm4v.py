from langchain.llms.base import LLM
from zhipuai import ZhipuAI
from langchain_core.messages.ai import AIMessage
from typing import Optional
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
zhipuai_api_key = os.getenv("zhipuai_api_key")

class ChatGLM4V(LLM):
    client: Optional[ZhipuAI] = None

    def __init__(self):
        super().__init__()
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatCogView3"

    def invoke(self, prompt: str):
        """调用 CogView-3 进行图像生成"""
        response = self.client.images.generate(
            model="cogview-3-flash",
            prompt=prompt
        )
        # 直接返回生成的图像 URL
        return AIMessage(content=response.data[0].url)

    def _call(self, prompt: str, stop=None, run_manager=None):
        """实现 _call 方法，以便可以被实例化"""
        return self.invoke(prompt)
