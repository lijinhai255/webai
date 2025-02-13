from langchain.llms.base import LLM
from zhipuai import ZhipuAI
from typing import Optional
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
zhipuai_api_key = os.getenv("zhipuai_api_key")

class ChatCogView3(LLM):
    client: Optional[ZhipuAI] = None

    def __init__(self):
        super().__init__()
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatCogView3"

    def invoke(self, prompt, stop=None, config=None):
        """调用 CogView-3 进行图像生成"""

        # ✅ 确保 `prompt` 为字符串
        if isinstance(prompt, list):
            prompt = prompt[-1].content.strip()
        else:
            prompt = str(prompt).strip()

        # 确保 `prompt` 不是空
        if not prompt:
            raise ValueError("输入的 prompt 不能为空")

        response = self.client.images.generations(
            model="cogview-3-flash",
            prompt=prompt
        )

        # ✅ 打印 API 响应，查看返回数据
        print("ZhipuAI API Response:", response)

        # ✅ 正确解析 API 响应
        if not response or not hasattr(response, "data") or not response.data:
            raise ValueError(f"API 响应数据无效: {response}")

        # ✅ 直接提取图片 URL
        image_url = response.data[0].url
        if not image_url:
            raise ValueError(f"API 没有返回有效的图片 URL: {response}")

        return image_url  # ✅ 直接返回字符串，而不是 AIMessage

    def _call(self, prompt, stop=None, run_manager=None, config=None):
        """确保 `LangChain` 兼容"""
        return self.invoke(prompt, stop=stop, config=config)
