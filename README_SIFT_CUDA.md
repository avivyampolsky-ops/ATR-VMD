# GPU Accelerated SIFT for ATR-VMD

This branch introduces integration with **CudaSift** (and placeholder support for **PopSift**) to enable GPU-accelerated SIFT feature extraction for Homography registration.

## Requirements

1.  **NVIDIA GPU** with CUDA support.
2.  **CUDA Toolkit** (e.g., v11.x or v12.x) installed and available in `$PATH` (providing `nvcc`).
3.  **OpenCV with CUDA**: Although this implementation uses external libraries for SIFT, the base system relies on OpenCV CUDA modules (`opencv_core`, `opencv_cudawarping`, etc.).

## Installation

### 1. External Libraries
The build system expects the external libraries to be present in `modules/3rdparty`.

*   **CudaSift**: Included via git clone.
    ```bash
    mkdir -p modules/3rdparty
    cd modules/3rdparty
    git clone https://github.com/Celebrandil/CudaSift.git
    ```

*   **PopSift** (Experimental/Placeholder):
    ```bash
    cd modules/3rdparty
    git clone https://github.com/PopSift/pop-sift.git
    ```
    *Note: PopSift integration is currently disabled in `setup_translation_gpu_cpp.py` due to build complexity.*

### 2. Build Extensions
Run the setup script. It will detect `CudaSift` and enable the `ENABLE_CUDASIFT` definition.

```bash
cd modules
python setup_translation_gpu_cpp.py build_ext --inplace
```

## Configuration

To use GPU SIFT, update your `config.yaml`:

```yaml
registration:
  mode: homography
  homography:
    feature_extractor: CUDA_SIFT  # Use "CUDA_SIFT" for CudaSift integration
    matcher: BF                   # Brute Force matching (run on CPU currently)
```

## Testing

A test script `test_fps.py` is provided to compare the performance of CPU SIFT vs. CUDA SIFT.

```bash
python test_fps.py
```

*Note: You must have a valid video file or image directory referenced in the script or config.*

## Implementation Details

*   **CudaSift Integration**:
    *   Source files from `modules/3rdparty/CudaSift` are compiled directly into the `_translation_gpu_cpp` extension.
    *   The `HomographyTranslationGPUCpp` class intercepts `feature_extractor="CUDA_SIFT"` and routes calls to `ExtractSift` from the CudaSift library.
    *   Keypoints and descriptors are converted back to OpenCV format (`cv::KeyPoint`, `cv::Mat`) for compatibility with the existing CPU-based Matchers (`cv::BFMatcher`, etc.).
    *   *Limitation*: Matching is still performed on the CPU. Future work could move matching to GPU using `cv::cuda::DescriptorMatcher` or CudaSift's matching functions.

*   **PopSift Integration**:
    *   Stubbed out. Requires linking against a pre-built PopSift library or a more complex CMake-based build process.
