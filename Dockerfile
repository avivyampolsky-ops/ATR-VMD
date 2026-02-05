# Base image for Jetson Orin (JetPack 6.x / L4T 36.x)
# We use dustynv/l4t-pytorch which is the standard for Jetson containers.
# Defaulting to r36.4.0 (JetPack 6.2) as requested.
# If this tag is unavailable, users can override via --build-arg BASE_IMAGE=...
ARG BASE_IMAGE=dustynv/l4t-pytorch:r36.4.0
FROM ${BASE_IMAGE}

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
# Ensure CUDA compiler is in PATH (standard location on Jetson)
ENV PATH=/usr/local/cuda/bin:${PATH}
ENV PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig

# Install system dependencies
# Note: 'python3-opencv' from apt might be CPU-only.
# dustynv images often come with OpenCV installed. We install dev headers.
# Added libopencv-contrib-dev for xfeatures2d support
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-dev \
    libopencv-dev \
    libopencv-contrib-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# We check if pip is installed/upgraded
RUN pip3 install --upgrade pip || true
# We explicitly add standard PyPI to ensure generic packages like PyYAML can be found
# even if the Jetson-specific index is unreachable.
RUN pip3 install --index-url https://pypi.org/simple --extra-index-url https://pypi.ngc.nvidia.com \
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
