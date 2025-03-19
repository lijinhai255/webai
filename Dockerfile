FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update && apt-get install -y \
    build-essential \
    libmysqlclient-dev \
    libgmp-dev \
    # 添加其他需要的系统依赖项

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "uvicorn", "chat_glm4:app", "--reload", "--port", "8000" ]