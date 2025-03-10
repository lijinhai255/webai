import os
import time
import streamlit as st
from LLM.img_videox import ChatCogVideoX
import cv2
from urllib.request import urlretrieve

def get_last_frame(video_url):
    # 临时下载视频
    temp_video_path = "./temp_video.mp4"
    urlretrieve(video_url, temp_video_path)
    
    # 打开视频
    cap = cv2.VideoCapture(temp_video_path)
    
    # 获取视频总帧数
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 设置读取位置为最后一帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    
    # 读取最后一帧
    ret, last_frame = cap.read()
    
    # 释放资源
    cap.release()
    
    # 删除临时视频文件
    os.remove(temp_video_path)
    
    if ret:
        # 保存最后一帧
        last_frame_path = "./last_frame.jpg"
        cv2.imwrite(last_frame_path, last_frame)
        return last_frame_path
    return None

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

    # **在这里用手动查询按钮，而不是自动轮询**
    if st.session_state.img2video_task_id:
        if st.button("🔍 查询进度"):
            with st.spinner("正在查询视频状态..."):
                result = cogvideo.get_video_result(st.session_state.img2video_task_id)

                if "video_url" in result:
                    # 生成成功
                    st.video(result["video_url"])
                    
                    # 获取视频最后一帧作为封面
                    last_frame_path = get_last_frame(result["video_url"])
                    if last_frame_path:
                        st.image(last_frame_path, caption="🎬 视频最后一帧")
                        os.remove(last_frame_path)  # 清理临时文件
                        
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