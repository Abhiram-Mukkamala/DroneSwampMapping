FROM python:3.10-slim

# System dependencies for OpenCV headless & health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Layer 1: PyTorch CPU (~192MB - downloads reliably from pytorch.org)
RUN pip install --no-cache-dir --default-timeout=300 \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Layer 2: OpenCV headless (~40MB instead of 74MB full opencv)
RUN pip install --no-cache-dir --default-timeout=300 opencv-python-headless

# Layer 3: Ultralytics WITHOUT its opencv-python dep (we have headless above)
#   Install ultralytics --no-deps, then its remaining deps explicitly
RUN pip install --no-cache-dir --no-deps ultralytics && \
    pip install --no-cache-dir --default-timeout=300 \
    matplotlib scipy pandas seaborn tqdm psutil py-cpuinfo pyyaml requests \
    ultralytics-thop

# Layer 4: FastAPI + web server deps (small packages)
RUN pip install --no-cache-dir fastapi uvicorn python-multipart pillow

# Copy application code and pre-downloaded YOLOv8 weights
COPY main.py .
COPY yolov8n.pt .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
