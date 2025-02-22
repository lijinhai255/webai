# my_streamlit_app/LLM/cogvideox.py

import time
import os
from typing import Optional
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from langchain.llms.base import LLM

# ✅ 加载环境变量
load_dotenv()  # 会去读取同目录或更上层的 .env 文件
zhipuai_api_key = os.getenv("zhipuai_api_key")


class ChatCogVideoX(LLM):
    client: Optional[ZhipuAI] = None

    def __init__(self):
        super().__init__()
        # 如果没有 API Key，会导致请求失败，请确保 .env 里已经配置好
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatCogVideoX"

    def invoke(self, prompt: str) -> str:
        """✅ 提交视频生成任务"""
        try:
            response = self.client.videos.generations(
                model="cogvideox-flash",
                prompt=prompt,
                quality="quality",
                with_audio=True,
                size="1080x1920",  # 视频分辨率，支持最高 4K（如: "3840x2160"）
                fps=30,           # 帧率，可选为30或60
            )

            if not response or not hasattr(response, "id"):
                return f"❌ API 请求失败: {response}"

            task_id = response.id  # ✅ 任务 ID
            print(f"✅ 任务提交成功，任务ID: {task_id}")

            return task_id  # 先返回task_id，等前端/其他逻辑再查询

        except Exception as e:
            return f"❌ 生成视频失败: {str(e)}"

    def get_video_result(self, task_id: str) -> dict:
        """✅ 轮询查询视频生成状态，并返回视频 URL"""
        try:
            max_retries = 18  # 最多查询 18 次（3 分钟）
            wait_time = 10    # 每次等待 10 秒

            for attempt in range(max_retries):
                time.sleep(wait_time)

                task_response = self.client.videos.retrieve_videos_result(id=task_id)

                print(f"🔄 查询任务状态，第 {attempt + 1} 次尝试，任务状态: {task_response.task_status}")

                if not task_response or not hasattr(task_response, "task_status"):
                    return {"error": f"❌ 查询任务失败: {task_response}"}

                if task_response.task_status == "SUCCESS":
                    # 注意 video_result 是列表
                    video_list = task_response.video_result
                    if not video_list or not video_list[0].url:
                        return {"error": "❌ 视频 URL 无效"}

                    return {
                        "video_url": video_list[0].url,
                        "cover_url": video_list[0].cover_image_url
                    }

                if task_response.task_status == "FAIL":
                    return {"error": "❌ 视频生成失败"}

            return {"error": "⏳ 任务超时，请稍后再试"}

        except Exception as e:
            return {"error": f"❌ 查询失败: {str(e)}"}

    def _call(self, prompt: str, stop=None, run_manager=None):
        """✅ 兼容 LangChain 调用"""
        return self.invoke(prompt)
