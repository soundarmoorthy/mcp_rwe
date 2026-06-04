FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9090
ENV MCP_TRANSPORT=streamable-http

CMD ["python", "server.py"]

