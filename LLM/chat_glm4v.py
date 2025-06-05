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
        return "ChatGLM4V"

    def invoke(self, prompt: str):
        """调用 GLM-4V-Flash 进行图像理解"""
        if isinstance(prompt, list):
            # 尝试从消息中提取图像URL
            for message in prompt:
                # 如果消息中包含图像URL，将其与用户文本组合
                if hasattr(message, 'content') and isinstance(message.content, str):
                    prompt = message.content
                    break
        
        response = self.client.chat.completions.create(
            model="glm-4v-flash",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content
        return AIMessage(content=result)

    def _call(self, prompt: str, stop=None, run_manager=None):
        """实现 _call 方法，以便可以被实例化"""
        return self.invoke(prompt)
        
    def stream(self, prompt, config={}, history=None):
        if history is None:
            history = []
        if isinstance(prompt, list):
            prompt = prompt[-1].content  # 取最新的用户输入

        history.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model="glm-4v-flash",
            messages=history,
            stream=True
        )
        for chunk in response:
            yield chunk.choices[0].delta.content