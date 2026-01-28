# Base image for Jetson Orin (JetPack 6.x / L4T 36.x)
# We use the official L4T PyTorch image which usually includes CUDA and OpenCV.
FROM nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.3-py3

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install \
    numpy \
    pyyaml \
    tqdm \
    pybind11 \
    setuptools

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Setup dependencies (clone CudaSift/PopSift) and build extensions
# We make the script executable and run it.
RUN chmod +x setup_dependencies.sh && \
    ./setup_dependencies.sh

# Default command
CMD ["python3", "main.py"]
