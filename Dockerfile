FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "uvicorn", "chat_glm4:app", "--reload", "--port", "8000" ]

#CMD [ "python", "./your-daemon-or-script.py" ]
