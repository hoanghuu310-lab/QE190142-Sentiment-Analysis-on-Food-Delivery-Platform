FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Lệnh mặc định giữ cho container chạy ngầm (chờ chạy script thủ công)
CMD ["tail", "-f", "/dev/null"]