# GPU Accelerated SIFT for ATR-VMD

This branch introduces integration with **CudaSift** and **PopSift** to enable GPU-accelerated SIFT feature extraction for Homography registration.

## Requirements

1.  **NVIDIA GPU** with CUDA support.
2.  **CUDA Toolkit** (e.g., v11.x or v12.x) installed and available in `$PATH` (providing `nvcc`).
3.  **OpenCV with CUDA**: The system relies on OpenCV CUDA modules (`opencv_core`, `opencv_cudawarping`, etc.).

## Installation

### 1. Setup Dependencies & Build
A unified script is provided to clone the external libraries (`CudaSift`, `PopSift`) and build the C++ extensions.

```bash
chmod +x setup_dependencies.sh
./setup_dependencies.sh
```

This script will:
1.  Clone `CudaSift` into `modules/3rdparty/CudaSift`.
2.  Clone `PopSift` into `modules/3rdparty/PopSift`.
3.  Compile the C++ extensions (`_translation_gpu_cpp`, etc.) using `nvcc` for the CUDA portions.

### 2. Docker (Jetson Orin)
For Jetson deployment, use the provided `install.sh` which wraps the Docker build process:

```bash
chmod +x install.sh
./install.sh run
```

## Configuration

To use GPU SIFT, update your `config.yaml`:

```yaml
registration:
  mode: homography
  homography:
    # Options: "SIFT" (CPU), "CUDA_SIFT" (CudaSift), "POP_SIFT" (PopSift)
    feature_extractor: CUDA_SIFT
    matcher: BF
```

## Testing

A test script `test_fps.py` is provided to compare the performance of CPU SIFT vs. CUDA SIFT vs. PopSift.

```bash
python test_fps.py
```

## Implementation Details

*   **CudaSift Integration**:
    *   Directly compiled into the extension.
    *   Optimized for standard usage.
    *   Memory is managed automatically.

*   **PopSift Integration**:
    *   Directly compiled into the extension (bypassing CMake).
    *   **Note**: PopSift typically requires a CMake build system. We manually generate the required `sift_config.h` during build to enable integration within the Python setuptools environment.
    *   Use with `feature_extractor: POP_SIFT`.
