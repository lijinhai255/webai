import streamlit as st
from functools import lru_cache

# Xunfei API credentials（请替换为您的实际配置）
APPID = "414dfd51"
APISecret = "OTJmYjQ4YmMzMTVkY2E5MTE5Y2RlY2Mx"
APIKey = "bb6f62671318f6009c8c7ba61e088495"
CERT_PATH = "/path/to/your/certificate.pem"

class XunfeiSTT:
    # ...（保持原有类定义不变）

@st.cache(maxsize=None)  # ✅ 移至模块级别
def load_config():
    return {
        "chat_history": [],
        "speech_errors": []
    }

def main():
    st.title("🎙️ 语音识别与 ChatGLM4 对话")
    
    # 初始化全局会话状态
    st.session_state.chat_history = load_config()["chat_history"]
    st.session_state.speech_errors = load_config()["speech_errors"]
    
    # 初始化服务实例
    stt = XunfeiSTT()
    chat_glm = ChatGLM4()
    
    # 显示控制面板
    voice_button = st.button("🎤 开始/停止语音识别", key="voice_control", 
                             on_click=lambda: stt.toggle_listening())
    
    # 显示状态信息
    with st.sidebar:
        st.markdown("### 📊 状态监控")
        st.text(f"错误日志: {stt.last_error or '无'}")
        st.text(f"识别队列: {stt.text_queue.qsize()}")
    
    # 处理用户输入
    user_input = st.chat_input("输入文字或使用语音...", key='user_input')
    
    # 处理文本消息
    def process_input(text):
        st.session_state.chat_history.append({
            "role": "user",
            "content": text
        })
        with st.chat_message("user"):
            st.markdown(text)
        
        response_text = ""
        for chunk in chat_glm.stream([HumanMessage(content=text)]):
            response_text += chunk
            st.experimental_rerun()
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text
        })
    
    # 处理语音消息
    def process_speech():
        while True:
            try:
                text = stt.text_queue.get_nowait().strip()
                if not text:
                    continue
                process_input(text)
                st.experimental_rerun()
            except queue.Empty:
                break
    
    # 启动后台线程
    if not hasattr(process_speech, 'running'):
        process_thread = threading.Thread(target=process_speech)
        process_thread.daemon = True
        process_thread.start()
        process_speech.running = True

    # 显示聊天记录
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

if __name__ == "__main__":
    main()