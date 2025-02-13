import streamlit as st
import os
from utils.resume_analyzer import analyze_resume
from utils.resume_generator import generate_resume_from_template
import openai
print(os.getenv('OPEN_API_KEY'))
OPENAI_API_KEY= os.getenv('OPEN_API_KEY')

# 设置 OpenAI API 密钥
openai.api_key = os.getenv(OPENAI_API_KEY)

# Streamlit UI
st.title("AI 简历优化与生成工具")

# 1. 上传简历文件
st.header("1. 上传简历文件")
uploaded_file = st.file_uploader("上传你的简历", type=["pdf", "docx", "txt"])


def analyze_resume_with_ai(resume_text):
    pass


if uploaded_file is not None:
    # 显示上传的文件名
    st.write(f"上传的文件: {uploaded_file.name}")

    # 调用简历分析函数
    resume_text = analyze_resume(uploaded_file)

    st.subheader("简历内容分析")
    st.text_area("简历分析结果", value=resume_text, height=300)

    # 提供简历分析后进一步优化的功能
    resume_analysis_button = st.button("进一步优化简历")
    if resume_analysis_button:
        optimized_resume = analyze_resume_with_ai(resume_text)
        st.subheader("优化后的简历内容")
        st.text_area("优化后的简历内容", value=optimized_resume, height=300)

# 2. 选择简历模板
st.header("2. 选择简历模板")
templates = os.listdir("templates")
template_choice = st.selectbox("选择简历模板", templates)


def read_template_description(template_choice):
    pass


if template_choice:
    st.subheader(f"选择模板：{template_choice}")

    # 读取模板描述（假设每个模板有描述信息）
    template_description = read_template_description(template_choice)
    st.write(template_description)

    # 提供简历内容输入框，用户可以选择继续编辑或者使用分析后的结果
    resume_content = st.text_area("输入简历内容（或使用分析结果）", value=resume_text, height=300)

    # 生成简历按钮
    if st.button("生成简历"):
        if resume_content.strip():
            # 调用简历生成函数
            resume = generate_resume_from_template(resume_content, template_choice)
            st.subheader("生成的简历")
            st.text_area("生成的简历内容", value=resume, height=500)
            st.download_button("下载简历", resume, "generated_resume.pdf", "application/pdf")
        else:
            st.error("请输入简历内容或使用分析结果！")


# 简历优化分析函数（假设调用 OpenAI API）
def analyze_resume_with_ai(resume_text):
    prompt = f"优化并分析以下简历内容，给出语言改进建议：\n{resume_text}"

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        temperature=0.7
    )

    return response.choices[0].text.strip()



