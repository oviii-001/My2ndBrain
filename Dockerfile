FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir aiohttp curl_cffi cryptography httpx websockets Pillow

# Copy authentic Meta Muse AI library and server
COPY muse_ai ./muse_ai
COPY muse_bridge_server.py .

ENV PORT=7860
EXPOSE 7860

CMD ["python", "muse_bridge_server.py"]
