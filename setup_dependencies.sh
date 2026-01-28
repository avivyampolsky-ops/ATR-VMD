#!/bin/bash
set -e

# Directory where 3rdparty libraries should reside
THIRDPARTY_DIR="modules/3rdparty"
mkdir -p "$THIRDPARTY_DIR"

echo "=== Setting up Dependencies ==="

# 1. Fetch CudaSift
if [ ! -d "$THIRDPARTY_DIR/CudaSift" ]; then
    echo "Cloning CudaSift..."
    git clone https://github.com/Celebrandil/CudaSift.git "$THIRDPARTY_DIR/CudaSift"
else
    echo "CudaSift already present."
fi

# 2. Fetch PopSift
if [ ! -d "$THIRDPARTY_DIR/PopSift" ]; then
    echo "Cloning PopSift..."
    git clone https://github.com/PopSift/pop-sift.git "$THIRDPARTY_DIR/PopSift"
else
    echo "PopSift already present."
fi

# 3. Build Extensions
echo "=== Building C++ GPU Extensions ==="
cd modules
if command -v nvcc >/dev/null 2>&1; then
    python3 setup_translation_gpu_cpp.py build_ext --inplace
else
    echo "WARNING: 'nvcc' not found. GPU extensions will likely fail to build or will be built without CUDA."
    # We attempt build anyway, the setup script handles checking nvcc and skipping .cu if needed,
    # but for SIFT/PopSift specifically, we need nvcc.
    python3 setup_translation_gpu_cpp.py build_ext --inplace || echo "Build failed (expected if no GPU/CUDA present)."
fi
cd ..

echo "=== Setup Complete ==="
