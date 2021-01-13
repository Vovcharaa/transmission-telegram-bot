FROM python:3.9 as build
WORKDIR /app
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt .
RUN pip install wheel
RUN python3 -m pip install -r requirements.txt --no-cache-dir

FROM python:3.9-slim
WORKDIR /app
COPY --from=build /app /app
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY . /app
EXPOSE 8080/tcp
CMD ["python", "-m", "transmission-telegram-bot"]
