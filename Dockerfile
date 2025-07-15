FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV HF_HOME=/app/cache
RUN mkdir -p /app/cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x start.sh
EXPOSE 8000
CMD ["./start.sh"]
