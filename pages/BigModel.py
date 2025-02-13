import streamlit as st
from langchain.schema import HumanMessage
from LLM.chat_glm4 import ChatGLM4
from LLM.chat_glm4v import ChatGLM4V
from LLM.cogview3 import ChatCogView3
from LLM.cogvideox import ChatCogVideoX

# 初始化 LLM
llm_models = {
    "GLM-4 Flash（文本）": ChatGLM4(),
    "GLM-4V Flash（图像理解）": ChatGLM4V(),
    "CogView-3 Flash（图像生成）": ChatCogView3(),
    "CogVideoX Flash（视频生成）": ChatCogVideoX()
}

# Streamlit 界面
st.title('💡 AI 多模型 Chatbot')

# 选择大模型
model_choice = st.selectbox("请选择模型：", list(llm_models.keys()))

# 使用 session_state 存储对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 显示聊天历史记录
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        if "图片" in chat["type"]:  # ✅ 如果是图片
            st.image(chat["content"], caption="AI 生成的图片", use_container_width=True)  # ✅ 移除 unsafe_allow_html
        elif "视频" in chat["type"]:  # ✅ 如果是视频
            st.video(chat["content"])
        else:  # ✅ 默认文本
            st.markdown(chat["content"])

# 用户输入框
user_input = st.chat_input("请输入你的消息..." if "文本" in model_choice else "请上传图片或输入描述")

if user_input:
    # 记录用户输入
    st.session_state.chat_history.append({"role": "user", "content": user_input, "type": "text"})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 调用 LLM 获取 AI 响应
    messages = [HumanMessage(content=user_input)]
    selected_llm = llm_models[model_choice]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()  # 占位符
        response_text = ""

        if isinstance(selected_llm, ChatGLM4) or isinstance(selected_llm, ChatGLM4V):
            # ✅ 文本输出
            for chunk in selected_llm.stream(messages):
                if isinstance(chunk, str):
                    response_text += chunk
                else:
                    response_text += str(chunk)

                response_placeholder.write(response_text)  # 实时更新文本
            st.session_state.chat_history.append({"role": "assistant", "content": response_text, "type": "text"})

        elif isinstance(selected_llm, ChatCogView3):
            # ✅ 生成图片
            image_url = selected_llm.invoke(user_input)
            st.image(image_url, caption="AI 生成的图片", use_container_width=True)
            st.session_state.chat_history.append({"role": "assistant", "content": image_url, "type": "图片"})

        elif isinstance(selected_llm, ChatCogVideoX):
            # ✅ 生成视频
            video_url = selected_llm.invoke(user_input)
            st.video(video_url)
            st.session_state.chat_history.append({"role": "assistant", "content": video_url, "type": "视频"})
