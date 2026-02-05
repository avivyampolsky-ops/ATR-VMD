#!/bin/bash
set -e

# Directory where 3rdparty libraries should reside
THIRDPARTY_DIR="modules/3rdparty"
mkdir -p "$THIRDPARTY_DIR"

echo "=== Setting up Dependencies ==="

# Helper function to check if directory is empty
is_empty() {
    [ -z "$(ls -A "$1" 2>/dev/null)" ]
}

# 1. Fetch CudaSift
if [ ! -d "$THIRDPARTY_DIR/CudaSift" ] || is_empty "$THIRDPARTY_DIR/CudaSift"; then
    echo "Cloning CudaSift..."
    rm -rf "$THIRDPARTY_DIR/CudaSift"
    git clone https://github.com/Celebrandil/CudaSift.git "$THIRDPARTY_DIR/CudaSift"
else
    echo "CudaSift already present."
fi

# 2. Fetch Popcorn (Required by PopSift)
if [ ! -d "$THIRDPARTY_DIR/Popcorn" ] || is_empty "$THIRDPARTY_DIR/Popcorn"; then
    echo "Cloning Popcorn..."
    rm -rf "$THIRDPARTY_DIR/Popcorn"
    git clone https://github.com/PopSift/popcorn.git "$THIRDPARTY_DIR/Popcorn"
else
    echo "Popcorn already present."
fi

# 3. Fetch PopSift
if [ ! -d "$THIRDPARTY_DIR/PopSift" ] || is_empty "$THIRDPARTY_DIR/PopSift"; then
    echo "Cloning PopSift..."
    rm -rf "$THIRDPARTY_DIR/PopSift"
    git clone https://github.com/alicevision/PopSift.git "$THIRDPARTY_DIR/PopSift"
else
    echo "PopSift already present."
fi

# 4. Generate PopSift Config Header
POPSIFT_CONFIG_FILE="$THIRDPARTY_DIR/PopSift/src/popsift/sift_config.h"
echo "Generating $POPSIFT_CONFIG_FILE..."
mkdir -p "$(dirname "$POPSIFT_CONFIG_FILE")"
cat > "$POPSIFT_CONFIG_FILE" <<EOF
/*
 * Copyright 2016, Simula Research Laboratory
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#pragma once

#define POPSIFT_IS_DEFINED(F)   F() == 1
#define POPSIFT_IS_UNDEFINED(F) F() == 0

// Standard configs for typical CUDA card
#define POPSIFT_HAVE_SHFL_DOWN_SYNC()     1
#define POPSIFT_DISABLE_GRID_FILTER()     0
EOF

# Debug: Find xfeatures2d.hpp to help diagnose build issues
echo "Debugging: Searching for xfeatures2d.hpp..."
find /usr -name "xfeatures2d.hpp" || true

# 5. Build Extensions
echo "=== Building C++ GPU Extensions ==="
cd modules
if command -v nvcc >/dev/null 2>&1; then
    python3 setup_translation_gpu_cpp.py build_ext --inplace
else
    echo "WARNING: 'nvcc' not found. GPU extensions will likely fail to build or will be built without CUDA."
    python3 setup_translation_gpu_cpp.py build_ext --inplace || echo "Build failed (expected if no GPU/CUDA present)."
fi
cd ..

echo "=== Setup Complete ==="
