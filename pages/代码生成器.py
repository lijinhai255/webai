import streamlit as st
from zhipuai import ZhipuAI
import json
import os

# 初始化智谱AI客户端
zhipuai_api_key = os.getenv("zhipuai_api_key")
client = ZhipuAI(api_key=zhipuai_api_key)

# 页面配置
st.set_page_config(page_title="Vue模板代码生成器", layout="wide")

# 初始化界面
st.title("🚀 Vue模板代码生成器")

# 左侧输入区域
with st.sidebar:
    st.header("API 配置")
    api_method = st.selectbox("请求方法", ["GET", "POST", "PUT", "DELETE"])
    api_url = st.text_input("API 路径", "/inspectionTask/listInfo")
    
    # 参数配置
    st.subheader("请求参数")
    params_text = st.text_area("参数列表 (每行一个，格式: 名称=类型=说明)", 
        """projectId=string=项目ID
name=string=巡检名称
status=number=状态
pageNum=number=页码
pageSize=number=每页数量""")

    # 返回值配置
    st.subheader("返回值字段")
    response_text = st.text_area("返回字段 (每行一个，格式: 字段名=说明)", 
        """name=巡检名称
hiddenDangerCount=隐患总数
majorHiddenDangerCount=重大隐患数量
genericHiddenDangerCount=一般隐患数量
status=状态
createTime=创建时间""")

# 主要内容区域
col1, col2 = st.columns([1, 1])

with col1:
    st.header("表格配置")
    show_selection = st.checkbox("显示选择列", value=False)
    table_height = st.text_input("表格高度", "calc(80vh - 70px)")
    
    # 搜索条件配置
    st.subheader("搜索条件")
    search_fields = st.multiselect(
        "选择搜索字段",
        ["name", "status"],
        ["name", "status"]
    )

def generate_vue_template():
    # 准备API信息
    api_info = {
        "method": api_method,
        "url": api_url,
        "params": [p.split("=") for p in params_text.split("\n") if p],
        "response": [r.split("=") for r in response_text.split("\n") if r]
    }

    # 准备表格配置
    table_config = {
        "showSelection": show_selection,
        "height": table_height,
        "columns": [{"prop": f[0], "label": f[1]} for f in api_info["response"]]
    }

    # 构建提示词
    prompt = f"""请根据以下信息生成使用<in-table>组件的Vue3代码：

API信息：
{json.dumps(api_info, indent=2, ensure_ascii=False)}

组件要求：
1. 使用自定义<in-table>组件，包含以下props：
   - :columns：表格列配置数组
   - :options：分页和请求配置对象
   - :show-selection：是否显示选择列
   - height：表格高度

2. 特殊列需要自定义插槽：
   - 图片列使用具名插槽#problemPicUrl，显示50x50缩略图
   - 操作列使用具名插槽#operate，包含编辑和整改记录按钮

3. 组件需包含以下功能：
   - 分页功能（与options.pagination绑定）
   - 自定义搜索表单（字段：{search_fields}）
   - 图片预览功能
   - 操作按钮事件处理

生成代码示例参考：
<template>
  <in-table
    :columns="columns"
    :options="options"
    :show-selection="false"
    height="calc(80vh - 70px)"
  >
    <template #problemPicUrl="{{ row }}">
      <el-image v-if="row.problemPicUrl" ...></el-image>
    </template>
    <template #operate="{{ row }}">
      <el-button @click="editHandler(row)">编辑</el-button>
    </template>
  </in-table>
</template>

请根据以下配置生成完整代码：
### 表格列配置 ###
{json.dumps(table_config['columns'], indent=2)}

### 分页配置 ###
当前页码：pageNum
每页数量：pageSize
总条数：total

### 需要实现的方法 ###
- editHandler(row) 编辑处理方法
- openRecordList(row) 查看整改记录
- handleSearch() 搜索方法
- resetSearch() 重置搜索
"""
    # 调用智谱AI接口
    response = client.chat.completions.create(
        model="glm-4",  # 使用GLM-4模型
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=0.2,
        max_tokens=3000
    )
    
    return response.choices[0].message.content

if st.button("生成代码"):
    with st.spinner("正在生成代码..."):
        try:
            generated_code = generate_vue_template()
            
            with col2:
                st.header("生成的代码")
                st.code(generated_code, language="vue")
                
                # 添加下载按钮
                st.download_button(
                    "下载Vue文件",
                    generated_code,
                    file_name="generated_vue_template.vue",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"生成代码时出错: {str(e)}")

# 添加使用说明
with st.expander("使用说明"):
    st.markdown("""
    1. 在左侧配置API信息和参数
    2. 在主区域配置表格显示选项
    3. 选择需要的搜索字段
    4. 点击"生成代码"按钮
    5. 查看并下载生成的Vue模板代码
    """)