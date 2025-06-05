import streamlit as st
from langchain.schema import HumanMessage

# 从 LLM 目录导入各模型
from LLM.chat_glm4 import ChatGLM4
from LLM.chat_glm4v import ChatGLM4V
from LLM.cogview3 import ChatCogView3
from LLM.cogvideox import ChatCogVideoX
from LLM.chat_glm_z1 import ChatGLMZ1  # 导入新添加的推理模型

# ✅ 初始化 LLM
llm_models = {
    "GLM-4-Flash-250414（语言模型）": ChatGLM4(),
    "GLM-4V-Flash（图像理解）": ChatGLM4V(),
    "CogView-3-Flash（图像生成）": ChatCogView3(),
    "CogVideoX-Flash（视频生成）": ChatCogVideoX(),
    "GLM-Z1-Flash（推理模型）": ChatGLMZ1()
}

# ✅ Streamlit 页面布局
st.title('💡 AI 多模型 Chatbot')

# 选择模型
model_choice = st.selectbox("请选择模型：", list(llm_models.keys()))
selected_llm = llm_models[model_choice]

# 初始化会话状态
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "video_task_id" not in st.session_state:
    st.session_state.video_task_id = None

# 显示聊天历史记录
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        if chat["type"] == "图片":
            st.image(chat["content"], caption="AI 生成的图片", use_container_width=True)
        elif chat["type"] == "视频":
            st.video(chat["content"])
        else:
            st.markdown(chat["content"])

# 用户输入框
user_input = st.chat_input("请输入你的消息...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input, "type": "text"})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        # A) 处理文本/图像理解/推理模型
        if isinstance(selected_llm, (ChatGLM4, ChatGLM4V, ChatGLMZ1)):
            response_text = ""
            for chunk in selected_llm.stream([HumanMessage(content=user_input)]):
                response_text += str(chunk)
                response_placeholder.write(response_text)
            st.session_state.chat_history.append({"role": "assistant", "content": response_text, "type": "text"})

        # B) 处理图像生成
        elif isinstance(selected_llm, ChatCogView3):
            image_url = selected_llm.invoke(user_input)
            st.image(image_url, caption="AI 生成的图片", use_container_width=True)
            st.session_state.chat_history.append({"role": "assistant", "content": image_url, "type": "图片"})

        # C) 处理视频生成
        elif isinstance(selected_llm, ChatCogVideoX):
            task_id = selected_llm.invoke(user_input)
            if task_id.startswith("❌"):
                st.error(task_id)
            else:
                st.session_state.video_task_id = task_id
                st.info(f"⏳ 视频任务提交成功，任务 ID: {task_id}，请稍后查询状态。")

# 视频查询按钮
if st.session_state.video_task_id:
    if st.button("🔍 查询视频状态"):
        with st.spinner("查询中..."):
            video_result = selected_llm.get_video_result(st.session_state.video_task_id)
            if "video_url" in video_result:
                st.video(video_result["video_url"])
                st.image(video_result["cover_url"], caption="🎬 视频封面")
                st.session_state.chat_history.append({"role": "assistant", "content": video_result["video_url"], "type": "视频"})
                st.session_state.video_task_id = None
            elif "error" in video_result:
                st.error(video_result["error"])