# LLM/img_videox.py

import os
import base64
from typing import Optional
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from langchain.llms.base import LLM

load_dotenv()
zhipuai_api_key = os.getenv("zhipuai_api_key")

def file_to_base64(local_path: str) -> str:
    """将本地图片读取并转为 data:image/jpeg;base64, 前缀的 Base64 字符串"""
    import base64
    with open(local_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return "data:image/jpeg;base64," + encoded

class ChatCogVideoX(LLM):
    client: Optional[ZhipuAI] = None

    def __init__(self):
        super().__init__()
        self.client = ZhipuAI(api_key=zhipuai_api_key)

    @property
    def _llm_type(self):
        return "ChatCogVideoX"

    def invoke(self, local_path: str = None, prompt: str = None) -> str:
        """提交图/文生视频任务并返回 task_id 或错误信息"""
        try:
            image_url = file_to_base64(local_path) if local_path else None

            response = self.client.videos.generations(
                model="cogvideox-2",
                image_url=image_url,
                prompt=prompt,
                quality="quality",
                with_audio=True,
                size="1080x1920",
                fps=60
            )
            if not response or not hasattr(response, "id"):
                return f"❌ API 请求失败: {response}"

            task_id = response.id
            print(f"✅ 任务提交成功: task_id={task_id}, status={response.task_status}")
            return task_id

        except Exception as e:
            return f"❌ 生成视频失败: {str(e)}"

    def get_video_result(self, task_id: str) -> dict:
        """
        查询视频生成状态:
          - 若成功: {"video_url": "...", "cover_url": "..."}
          - 若仍在处理: {"error": "PROCESSIN1G"}
          - 失败或异常: {"error": "..."}
        """
        try:
            result = self.client.videos.retrieve_videos_result(id=task_id)
            if not result or not hasattr(result, "task_status"):
                return {"error": f"❌ 查询任务失败: {result}"}

            status = result.task_status
            if status == "SUCCESS":
                video_list = result.video_result
                if video_list and video_list[0].url:
                    return {
                        "video_url": video_list[0].url,
                        "cover_url": video_list[0].cover_image_url
                    }
                else:
                    return {"error": "❌ 视频 URL 无效"}
            elif status == "FAIL":
                return {"error": "❌ 视频生成失败"}
            else:
                # PROCESSING
                return {"error": "PROCESSING"}

        except Exception as e:
            return {"error": f"❌ 查询失败: {str(e)}"}

    def _call(self, prompt: str, stop=None, run_manager=None):
        """LangChain 兼容接口，可忽略"""
        return self.invoke(prompt=prompt)
