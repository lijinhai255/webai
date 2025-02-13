import streamlit as st
from zhipuai import ZhipuAI
import pdfplumber
import docx
import os

# ✅ 1. 初始化 ZhipuAI（智谱AI）客户端
zhipuai_api_key = os.getenv("zhipuai_api_key")
client = ZhipuAI(api_key=zhipuai_api_key)

# ✅ 2. 侧边栏（参数调节）
st.sidebar.title("🔬 参数调节")
max_tokens = st.sidebar.slider("max_tokens", 256, 4096, 1024)
temperature = st.sidebar.slider("temperature", 0.0, 1.0, 0.7)
top_p = st.sidebar.slider("top_p", 0.0, 1.0, 0.9)

# ✅ 3. 页面标题
st.title("📄 AI 简历优化助手")
st.write("🔍 **智能优化简历，提供修改建议，并预测面试知识点与问题！**")

# ✅ 4. 用户输入（文本 or 文件）
user_input = st.text_area("✏️ 请输入你的简历信息", "", height=250)

uploaded_file = st.file_uploader("📂 或者上传简历文件（PDF / DOCX / TXT）", type=["pdf", "docx", "txt"])

# ✅ 5. 解析文件（如果用户上传了）
def extract_text_from_file(file):
    text = ""
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif file.type == "text/plain":
        text = file.read().decode("utf-8")
    return text

if uploaded_file:
    file_text = extract_text_from_file(uploaded_file)
    st.text_area("📌 解析后的简历内容", file_text, height=200)
    user_input = file_text  # 让文件内容进入 AI 处理流程

# ✅ 6. 生成 AI 优化简历、修改建议和面试预测
if st.button("🚀 优化简历"):
    if not user_input:
        st.warning("请输入简历信息或上传文件！")
    else:
        with st.spinner("AI 正在优化简历，请稍等..."):
            # **构建 AI 提示词**
            prompt = f"""
### 角色: 简历优化助手 (Resume Enhancer)
#### 目标：
1. **完善简历内容**，确保信息全面、丰富，并提升可读性。
2. **提供修改建议**，指出简历的不足并给出具体优化方向。
3. **面试准备**：
   - **知识点**：基于简历内容，列出应掌握的核心知识点。
   - **面试问题**：预测面试官可能提问的问题。

#### 用户简历：
{user_input}

请按照如下格式输出：
---
### **📄 优化后的简历**
（完善后的简历内容）

---
### **🔍 修改建议**
（简历的不足之处 + 具体优化建议）

---
### **🎯 面试知识点**
（基于简历，列出面试应掌握的知识）

---
### **💬 面试官可能会问的问题**
（结合行业和职位，列出常见的面试问题）
"""
            # **调用 AI 处理**
            response = client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            # **解析 AI 返回的结果**
            ai_response = response.choices[0].message.content

            # **展示优化后的简历**
            sections = ai_response.split("---")  # 按分隔符拆分
            if len(sections) >= 4:
                st.subheader("✅ **优化后的简历**")
                st.text_area("", sections[0].strip(), height=300)

                st.subheader("🔍 **修改建议**")
                st.markdown(sections[1].strip())

                st.subheader("🎯 **面试知识点**")
                st.markdown(sections[2].strip())

                st.subheader("💬 **面试官可能会问的问题**")
                st.markdown(sections[3].strip())

                # **提供下载功能**
                st.download_button("📥 下载优化简历", sections[0].strip(), file_name="optimized_resume.txt")

# ✅ 7. 版权信息
st.sidebar.markdown("---")
st.sidebar.markdown("💡 Created by hai | AI Resume Enhancer")
