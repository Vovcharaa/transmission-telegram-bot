FROM python:3.9-slim
RUN pip install wheel
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --no-cache-dir
COPY . /app
CMD python -m transsmision-telegram-bot