FROM python:3.11-slim

# Tạo thư mục làm việc
WORKDIR /app

# Copy file requirements trước để tận dụng cache
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose port MCP server (mặc định 9000)
EXPOSE 9000

# CMD để docker-compose override
CMD ["python", "mcp_pipe.py", "getassetprice.py"]
