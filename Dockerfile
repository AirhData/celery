FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV HF_HOME=/app/cache
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/cache

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
