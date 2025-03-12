import os
import time
import streamlit as st
from LLM.img_videox import ChatCogVideoX
from urllib.request import urlretrieve
from PIL import Image
import cv2
import tempfile
import requests

def download_video(url, temp_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    return False

def get_last_frame_from_video(video_url, output_path="./last_frame.jpg"):
    try:
        # 创建临时文件来保存视频
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video_path = temp_video.name
            
        # 下载视频到临时文件
        if not download_video(video_url, temp_video_path):
            raise Exception("无法下载视频")

        # 打开视频文件
        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频")

        # 获取总帧数
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames > 0:
            # 读取所有帧直到最后一帧
            last_frame = None
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                last_frame = frame

            if last_frame is not None:
                cv2.imwrite(output_path, last_frame)
                return output_path
            else:
                raise Exception("无法读取最后一帧")
        else:
            raise Exception("视频没有帧")

    except Exception as e:
        st.error(f"获取视频最后一帧失败: {str(e)}")
        return None
    
    finally:
        if 'cap' in locals():
            cap.release()
        # 清理临时文件
        if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)

def img2video_app():
    st.title("🎬 图生视频演示（手动查询）")

    # 初始化模型
    cogvideo = ChatCogVideoX()

    # 维护 session_state
    if "img2video_task_id" not in st.session_state:
        st.session_state.img2video_task_id = None
    if "uploaded_img_path" not in st.session_state:
        st.session_state.uploaded_img_path = None

    # 上传文件
    uploaded_file = st.file_uploader(
        label="📂 上传图片生成视频 (png/jpg/jpeg)",
        type=["png", "jpg", "jpeg"]
    )

    prompt = st.text_input("可选：输入文本描述以辅助生成")

    # 保存文件
    if uploaded_file:
        save_dir = "./uploads"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.image(file_path, caption="✅ 图片上传成功")
        st.session_state.uploaded_img_path = file_path

    # 提交生成任务 (只做一次)
    if st.session_state.uploaded_img_path:
        if st.button("🎬 开始生成视频"):
            with st.spinner("提交生成任务中..."):
                task_id = cogvideo.invoke(
                    local_path=st.session_state.uploaded_img_path,
                    prompt=prompt or None
                )
                if task_id.startswith("❌"):
                    st.error(task_id)
                else:
                    st.session_state.img2video_task_id = task_id
                    st.success(f"任务已提交, task_id={task_id}")
                    st.info("请稍后点击【查询进度】按钮。")

    # 手动查询进度
    if st.session_state.img2video_task_id:
        if st.button("🔍 查询进度"):
            with st.spinner("正在查询视频状态..."):
                result = cogvideo.get_video_result(st.session_state.img2video_task_id)

                if "video_url" in result:
                    # 生成成功
                    st.video(result["video_url"])
                    
                    # 获取最后一帧
                    last_frame_path = get_last_frame_from_video(result["video_url"])
                    if last_frame_path and os.path.exists(last_frame_path):
                        st.image(last_frame_path, caption="🎬 视频最后一帧")
                        os.remove(last_frame_path)  # 清理临时文件
                    
                    # 显示封面图（如果有）
                    if "cover_url" in result:
                        st.image(result["cover_url"], caption="🎬 视频封面")
                    
                    st.session_state.img2video_task_id = None  # 清空任务ID
                elif result.get("error") == "PROCESSING":
                    st.info("视频仍在处理中，请稍后再试。")
                else:
                    # 出错或失败
                    st.error(result["error"])
                    st.session_state.img2video_task_id = None

if __name__ == "__main__":
    img2video_app()