import streamlit as st
from zhipuai import ZhipuAI
import json
import os
import re

# 初始化智谱AI客户端
zhipuai_api_key = os.getenv("zhipuai_api_key")
client = ZhipuAI(api_key=zhipuai_api_key)

# 页面配置
st.set_page_config(page_title="Vue模板生成器", layout="wide")

# 初始化界面
st.title("Vue模板生成器")

# 初始化搜索字段列表
if "search_fields" not in st.session_state:
    st.session_state.search_fields = ["name", "status"]

# 左侧输入区域
with st.sidebar:
    st.header("API 配置")
    api_config_text = st.text_area(
        "粘贴API配置信息",
        """GET
/screen/monitorRelevance/infoList?projectId=&pageNum=&pageSize=
/**
* 设备id
*/
private String deviceId;

/**
* 自定义摄像头名称
*/
private String monitorName;

/**
* 硬盘录像机ID
*/
private String channelId;

/**
* 设备中的摄像头ID
*/
private String monitorId;
/**
* 类型（1：塔吊，2：升降机，3：物资）
*/
private Integer type;""",
        height=300,
    )

    # 解析API配置信息
    api_config = {}
    lines = api_config_text.split("\n")
    if lines:
        api_config["method"] = lines[0].split(" ")[0]
        api_config["url"] = lines[1].split("?")[0]

    params = []
    for line in lines[2:]:
        # 尝试匹配 Java 参数定义
        match = re.search(r"private\s+\w+\s+(\w+);\s*(/\*\*\s*\n\s*\*\s*(.*?)\s*\n\s*\*/)?", line)
        if match:
            param_name = match.group(1)
            comment = match.group(2) or ""
            params.append({"name": param_name, "description": comment.strip()})
        else:
            # 尝试匹配空格分隔的参数定义
            parts = line.split(" ")
            if len(parts) >= 2:
                params.append({"name": parts[0], "description": " ".join(parts[1:])})

    api_config["params"] = params

    # 自动填充参数
    if "method" in api_config:
        api_method = st.selectbox("请求方法", ["GET", "POST", "PUT", "DELETE"], index=["GET", "POST", "PUT", "DELETE"].index(api_config["method"]))
    if "url" in api_config:
        api_url = st.text_input("API 路径", api_config["url"])

    if "params" in api_config:
        st.subheader("查询参数")
        params_text_area = "\n".join([f"{param['name']} {param['description']}" for param in api_config["params"]])
        params_text = st.text_area("查询参数 (每行一个，格式: 名称 说明)", params_text_area)

    # 自动生成搜索配置
    if "search_fields" not in st.session_state:
        st.session_state.search_fields = ["name", "status"]

    st.subheader("搜索配置")

    # 手动添加选项
    new_search_field = st.text_input("添加搜索字段")
    if new_search_field and new_search_field not in st.session_state.search_fields:
        st.session_state.search_fields.append(new_search_field)

    st.session_state.search_fields = st.multiselect(
        "选择搜索字段",
        st.session_state.search_fields,
        st.session_state.search_fields,  # 使用更新后的搜索字段列表作为 default
        key="search_fields_sidebar"
    )

    # 返回值字段
    st.subheader("返回值字段")
    response_text = st.text_area(
        "返回值字段 (每行一个，格式: 字段名 说明)",
        """deviceId 设备ID
monitorName 摄像头名称
channelId 硬盘录像机ID
monitorId 摄像头ID
type 类型""",
    )

# 主要内容区域
col1, col2 = st.columns([1, 1])
with col1:
    st.header("表格配置")
    show_selection = st.checkbox("显示选择列", value=False)
    table_height = st.text_input("表格高度", "calc(80vh - 70px)")

    # 搜索条件配置
    st.subheader("搜索条件")
    search_fields_main = st.multiselect(
        "选择搜索字段", st.session_state.search_fields, st.session_state.search_fields, key="search_fields_main"
    )

    # 新增搜索表单配置
    st.subheader("搜索表单字段")
    search_form_fields = st.text_area(
        "搜索表单字段 (每行一个，格式: 字段名=类型=占位符)",
        """name=string=请输入巡检名称
status=number=请选择状态""",
    )

def generate_vue_template():
    # 从 st.session_state 中获取 search_fields
    search_fields = st.session_state.search_fields

    # 准备API信息
    api_info = {
        "method": api_method,
        "url": api_url,
        "params": [
            {"name": p.split(" ")[0], "description": " ".join(p.split(" ")[1:])}
            for p in params_text.split("\n")
            if p.strip()
        ],
        "response": [
            {"name": r.split(" ")[0], "description": " ".join(r.split(" ")[1:])}
            for r in response_text.split("\n")
            if r.strip()
        ],
    }

    # 准备表格配置
    table_config = {
        "showSelection": show_selection,
        "height": table_height,
        "columns": [
            {"prop": f["name"], "label": f.get("description", f["name"])}
            for f in api_info["response"]
        ],
    }

    # 准备搜索表单配置
    search_form_config = [
        {
            "field": f.split("=")[0],
            "type": f.split("=")[1],
            "placeholder": f.split("=")[2],
        }
        for f in search_form_fields.split("\n") 
        if f
    ]

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
   - 自定义搜索表单（字段：{st.session_state.search_fields}），使用<el-form>实现
   - 图片预览功能
   - 操作按钮事件处理
   - 实现搜索和重置搜索功能

4. 搜索表单字段配置：
{json.dumps(search_form_config, indent=2, ensure_ascii=False)}

5. options 使用 reactive 定义, 包含 url method data属性

生成代码示例参考：
<template>
  <el-form :model="form" :inline="true" style="height: 50px">
    <el-form-item v-for="item in searchForm" :key="item.field" :label="item.placeholder">
      <el-input v-if="item.type === 'string'" v-model="form[item.field]" :placeholder="item.placeholder" size="small"></el-input>
      <el-select v-else-if="item.type === 'number'" v-model="form[item.field]" size="small">
        <el-option v-for="(option, index) in statusOptions" :key="index" :value="option.value" :label="option.label"></el-option>
      </el-select>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" icon="el-icon-search" size="mini" @click="handleSearch">搜索</el-button>
      <el-button icon="el-icon-refresh" size="mini" @click="resetSearch">重置</el-button>
    </el-form-item>
  </el-form>
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

<script setup>
import { 'reactive' } from 'vue';

let options = reactive({{
    url: '{api_url}',
    method: '{api_method}',
    data: {{
        pageNum: 1,
        pageSize: 10,
        // 其他参数...
    }}
}});

// ... 其他代码 ...

</script>

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
    1. 在左侧配置API信息和参数""")