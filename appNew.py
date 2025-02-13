import streamlit as st
from langchain.schema import HumanMessage
from utils.llm import llm  # ✅ 引入封装好的 llm 实例

# Streamlit 页面标题
st.title("LangChain + Streamlit Chatbot")

with st.sidebar:
    st.write("侧边栏内容")
    st.sidebar.markdown("# Main page 🎈")

# 使用 session_state 存储对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 显示聊天历史记录
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# 用户输入框
user_input = st.chat_input("输入你的消息...")

if user_input:
    # 记录用户消息
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 在界面上显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 构造 LangChain 对话输入
    messages = [HumanMessage(content=user_input)]
    response = llm.invoke(messages)

    # 获取 AI 回复
    ai_response = response.content

    # 记录 AI 消息
    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # 在界面上显示 AI 响应
    with st.chat_message("assistant"):
        st.markdown(ai_response)
