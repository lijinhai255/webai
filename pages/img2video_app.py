import os
import time
import streamlit as st
from LLM.img_videox import ChatCogVideoX
from urllib.request import urlretrieve
from PIL import Image
import tempfile
import requests
from dotenv import load_dotenv

def download_video(url, temp_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    return False

def img2video_app():
    st.title("🎬 图生视频演示 - CogVideoX-Flash")

    # 检查API密钥是否存在
    load_dotenv()
    api_key = os.getenv("zhipuai_api_key")
    
    if not api_key:
        st.error("⚠️ 未检测到API密钥。请在 .env 文件中设置 zhipuai_api_key。")
        st.info("请创建一个 .env 文件，并添加以下内容：\n\n```\nzhipuai_api_key=您的智谱AI-API密钥\n```")
        return  # 如果没有API密钥，提前返回

    # 显示CogVideoX-Flash特性介绍
    with st.expander("✨ CogVideoX-Flash 功能特点", expanded=False):
        st.markdown("""
        - 🔊 **沉浸式AI音效**：智能识别场景元素，生成适配的音效组合
        - 🎬 **高清画质**：支持多种分辨率，最高可达4K超高清
        - ⏱️ **10秒视频时长**：满足更多场景需求
        - 🚀 **60fps高帧率**：流畅度大幅提升，捕捉每一个精彩瞬间
        """)

    # 初始化模型
    cogvideo = ChatCogVideoX()

    # 维护 session_state
    if "img2video_task_id" not in st.session_state:
        st.session_state.img2video_task_id = None
    if "uploaded_img_path" not in st.session_state:
        st.session_state.uploaded_img_path = None
    if "image_url" not in st.session_state:
        st.session_state.image_url = None

    # 创建两列布局用于输入方式选择
    col1, col2 = st.columns(2)
    
    with col1:
        input_method = st.radio("选择输入方式", ["上传图片", "图片URL"])
    
    # 根据选择的输入方式显示不同的输入界面
    if input_method == "上传图片":
        # 上传文件
        uploaded_file = st.file_uploader(
            label="📂 上传图片生成视频 (png/jpg/jpeg)",
            type=["png", "jpg", "jpeg"]
        )
        
        # 保存文件
        if uploaded_file:
            # 检查文件大小
            file_size_mb = uploaded_file.size / (1024 * 1024)  # 转换为MB
            if file_size_mb > 5:
                st.error("❌ 图片大小超过5MB限制，请上传更小的图片")
            else:
                save_dir = "./uploads"
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, uploaded_file.name)

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.image(file_path, caption=f"✅ 图片上传成功 (大小: {file_size_mb:.2f}MB)")
                st.session_state.uploaded_img_path = file_path
                st.session_state.image_url = None  # 清除另一种输入方式
    else:
        # 图片URL输入
        image_url = st.text_input("输入图片URL")
        if image_url:
            try:
                # 显示图片预览
                st.image(image_url, caption="✅ 图片URL预览")
                st.session_state.image_url = image_url
                st.session_state.uploaded_img_path = None  # 清除另一种输入方式
            except Exception as e:
                st.error(f"❌ 无法加载图片: {str(e)}")

    prompt = st.text_input("可选：输入文本描述以辅助生成")
    
    # AI音效提示（但不作为参数传递）
    st.info("🔊 CogVideoX-Flash 模型会自动为视频添加适合的AI音效")
    
    # 指定使用Flash模型
    st.success("🚀 当前使用的是 CogVideoX-Flash 模型，自动启用高帧率和高清画质")

    # 提交生成任务 (只做一次)
    if st.session_state.uploaded_img_path or st.session_state.image_url:
        submit_button = st.button("🎬 开始生成视频")
        if submit_button:
            with st.spinner("提交生成任务中..."):
                # 准备参数 - 只保留已知支持的参数
                params = {
                    "prompt": prompt or None
                }
                
                # 根据输入方式选择参数
                if st.session_state.uploaded_img_path:
                    params["local_path"] = st.session_state.uploaded_img_path
                else:
                    params["image_url"] = st.session_state.image_url
                
                # 调用API
                try:
                    task_id = cogvideo.invoke(**params)
                    
                    if isinstance(task_id, str) and task_id.startswith("❌"):
                        error_msg = task_id
                        if "1113" in error_msg or "欠费" in error_msg:
                            recharge_url = "https://open.bigmodel.cn/usercenter/overview"
                            st.error(f"{error_msg}")
                            st.markdown(f"[🔄 立即前往充值]({recharge_url})")
                        else:
                            st.error(error_msg)
                    else:
                        st.session_state.img2video_task_id = task_id
                        st.success(f"任务已提交, task_id={task_id}")
                        st.info("请稍后点击【查询进度】按钮。")
                except Exception as e:
                    st.error(f"提交任务失败: {str(e)}")

    # 手动查询进度
    if st.session_state.img2video_task_id:
        if st.button("🔍 查询进度"):
            with st.spinner("正在查询视频状态..."):
                try:
                    result = cogvideo.get_video_result(st.session_state.img2video_task_id)

                    if "video_url" in result:
                        # 生成成功
                        st.success("✅ 视频生成成功！")
                        
                        # 显示视频
                        st.video(result["video_url"])
                        
                        # 显示封面图（如果有）
                        if "cover_url" in result:
                            st.image(result["cover_url"], caption="🎬 视频封面")
                        
                        # 添加下载按钮
                        st.markdown(f"[📥 下载视频]({result['video_url']})")
                        
                        st.session_state.img2video_task_id = None  # 清空任务ID
                    elif result.get("error") == "PROCESSING":
                        st.info("⏳ 视频仍在处理中，请稍后再试。")
                    else:
                        # 出错或失败
                        error_msg = result.get('error', '未知错误')
                        st.error(f"❌ {error_msg}")
                        
                        # 如果是欠费错误，添加充值链接
                        if "1113" in str(error_msg) or "欠费" in str(error_msg):
                            recharge_url = "https://open.bigmodel.cn/usercenter/overview"
                            st.markdown(f"[🔄 立即前往充值]({recharge_url})")
                        
                        st.session_state.img2video_task_id = None
                except Exception as e:
                    st.error(f"查询失败: {str(e)}")
                    st.warning("服务调用失败，请检查API密钥是否有效。")

if __name__ == "__main__":
    img2video_app()