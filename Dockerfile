FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for cryptography & curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications and code
COPY scratch/MuseAI-API/pyproject.toml .
COPY scratch/MuseAI-API/muse_ai ./scratch/MuseAI-API/muse_ai
COPY scratch/muse_state ./scratch/muse_state
COPY muse_bridge_server.py .

# Install dependencies
RUN pip install --no-cache-dir aiohttp curl_cffi cryptography httpx websockets Pillow

ENV PORT=8130
EXPOSE 8130

CMD ["python", "muse_bridge_server.py"]
