FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p storage/uploads storage/frames storage/crops storage/outputs storage/models storage/database storage/logs storage/datasets

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "vms_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
