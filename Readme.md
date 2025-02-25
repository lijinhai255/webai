uvicorn chat_glm4:app --reload --port 8000 

# 删除现有虚拟环境
rm -rf venv

# 重新创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

pip install -r requirements.txt  # 如果有 requirements.txt 文件
# 或手动安装核心依赖：
pip install numpy==1.26.4 torch==2.1.0 sentence-transformers==0.11.0 langchain langchain-huggingface faiss


 # 激活虚拟环境
source venv/bin/activate

# 卸载当前 urllib3
pip uninstall urllib3

# 安装 urllib3 1.26.4（与您的代码兼容版本）
pip install urllib3==1.26.4