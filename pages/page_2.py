import streamlit as st
import  pandas as pd
import  numpy as np
import matplotlib.pyplot as plt
import requests
import plotly.express as px

st.title('hellow Streamlit !')

st.write('这是第一个应用')

st.header('这是二级标题')

st.text('普通文本')

st.code("print('Hellow Streamline')",language="python")

st.markdown("# Page 2 ❄️")
st.sidebar.markdown("# Page 2 ❄️")


st.markdown("## 数据展示")
df = pd.DataFrame(np.random.randn(5,3),columns=['A',"B","C"])

st.dataframe(df)
st.table(df) # 静态表格


st.markdown("## 用户输入 ")


name = st.text_input("请输入你的名字：")
age = st.number_input("请输入你的年龄：", min_value=0, max_value=100)
agree = st.checkbox("我同意条款")

st.write(name,age,agree)


st.markdown("## 按钮")

if st.button("点击我"):
    st.write("按钮被点击了！")

st.markdown("## 选择框")

option = st.selectbox("请选择一个选项", ["选项1", "选项2", "选项3"])

st.write(f"你选择了：{option}")

st.markdown("## 文件上传")

uploaded_file = st.file_uploader("上传文件", type=["csv", "txt"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

st.markdown("## 可视化")

fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [10, 20, 30, 40])
st.pyplot(fig)

st.markdown('动态交互（Session State）')

if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("增加计数"):
    st.session_state.counter += 1

st.write("计数:", st.session_state.counter)


st.markdown(" API 调用")


response = requests.get("https://api.github.com")
st.json(response.json())


st.markdown('数据分析仪表盘')
st.title("数据分析仪表盘")

df = px.data.gapminder()

year = st.slider("选择年份", min_value=int(df.year.min()), max_value=int(df.year.max()), step=5)
filtered_df = df[df.year == year]

fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp", size="pop", color="continent", log_x=True)
st.plotly_chart(fig)
