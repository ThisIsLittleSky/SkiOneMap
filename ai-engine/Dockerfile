FROM python:3.11-slim

WORKDIR /app

RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# torch + torchvision CPU 版本，先装防止 ultralytics 拉 CUDA 版覆盖
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    --trusted-host download.pytorch.org \
    torch==2.7.1 \
    torchvision==0.22.1

# 预下载 ResNet50 权重（person_reidentification 用）
RUN python -c "from torchvision.models import resnet50; resnet50(pretrained=True)"

# Python 依赖（torch/torchvision 已装，ultralytics 不会再拉 CUDA 版）
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 5 -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt

# 预下载 YOLO 模型（在 COPY 源码之前，利用缓存）
# 保留在 /app/ 一份，volume 挂载会遮住 /models/ 下的副本
RUN mkdir -p /data/chroma /models && \
    python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')" && \
    cp yolo11n.pt /models/yolo11n.pt

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY . .

EXPOSE 8001

ENTRYPOINT ["/docker-entrypoint.sh"]
