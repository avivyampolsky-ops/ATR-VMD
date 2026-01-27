# ATR-VMD (Automatic Target Recognition - Video Motion Detection)

ATR-VMD is a high-performance Video Motion Detection and Tracking system designed for developers. It leverages a hybrid Python/C++ architecture with optional GPU (CUDA) acceleration to perform real-time image registration, moving object detection, and tracking.

## Features

*   **Hybrid Architecture**: Core logic available in Python for flexibility and C++ for performance.
*   **GPU Acceleration**: Utilizes CUDA via OpenCV for intensive tasks like image registration and background subtraction.
*   **Robust Registration**: Supports both Homography and Translation-based registration to stabilize video feeds.
*   **Motion Detection**: Implements MOG2 (Mixture of Gaussians) background subtraction.
*   **Tracking**: Kalman Filter with IOU (Intersection over Union) matching for object tracking.
*   **Debug Tools**: Extensive visualization, timing summaries, and frame-by-frame debugging.

## Prerequisites

To build and run ATR-VMD, you need the following:

*   **Python 3.8+**
*   **C++ Compiler** (supporting C++17)
*   **OpenCV 4.x with CUDA support**: This is critical for the GPU-accelerated modules.
    *   Ensure `opencv_core`, `opencv_cudawarping`, `opencv_cudabgsegm`, etc., are available.
*   **Python Dependencies**:
    *   `numpy`
    *   `opencv-python` (or `opencv-contrib-python`)
    *   `PyYAML`
    *   `tqdm`
    *   `pybind11` (for building C++ extensions)
    *   `setuptools`

## Installation & Build

The performance-critical components are implemented in C++. You must compile these extensions before running the application.

1.  **Install Python Dependencies**:
    ```bash
    pip install numpy pyyaml tqdm pybind11 setuptools
    ```

2.  **Build C++ Extensions**:
    The build script is located in `modules/setup_translation_gpu_cpp.py`. Run the following command from the project root:

    ```bash
    cd modules
    python setup_translation_gpu_cpp.py build_ext --inplace
    cd ..
    ```

    *Note: Ensure your `PKG_CONFIG_PATH` is correctly set if OpenCV is installed in a non-standard location.*

## Configuration

The system is configured via `config.yaml`. Below is a detailed explanation of the available sections and parameters.

### General
*   `use_cpp`: (bool) Enable C++ implementations for registration and detection.
*   `use_cuda`: (bool) Enable CUDA GPU acceleration.
*   `input_is_gray`: (bool) Force input processing in grayscale.

### Debug
*   `debug_mode`: (bool) Enable debug logging and outputs.
*   `draw_output`: (bool) Render tracked bounding boxes and masks to video/images.
*   `show_pipeline`: (bool) Print the active processing pipeline (CPU/GPU/Python/C++) at startup.
*   `enable_timing`: (bool) Collect and print detailed performance metrics.
*   `start_frame`: (int) Frame index to start processing from.
*   `end_frame`: (int) Frame index to stop at (-1 for end of stream).
*   `fps`: (float) Override FPS for debug video output.

### Registration
Controls how the image is stabilized against a reference frame.

*   `mode`: "homography" or "translation".
*   `downscale_factor`: (float) Scale factor for registration calculation (e.g., 0.75).
*   `reference_window_ms`: (float) Time in ms to keep a reference frame before re-anchoring.
*   **Homography Settings**:
    *   `feature_extractor`: "FAST_BRIEF", "ORB", "AKAZE", "BRISK", "SIFT".
    *   `matcher`: "KNN", "BF" (Brute Force), "FLANN".
    *   `knn_ratio`: (float) Lowe's ratio test threshold.
    *   `ransac_reproj_threshold`: (float) Max reprojection error for RANSAC.
    *   `min_inliers`: (int) Minimum inliers required to accept a homography.
*   **Translation Settings**:
    *   `method`: "phase" (Phase Correlation).
    *   `max_shift`: (float) Maximum allowed pixel shift.
    *   `phase_use_cached_fft`: (bool) Optimize FFT by caching.
    *   `phase_response_threshold`: (float) Minimum response to accept a shift.

### Detection
Controls the MOG2 background subtractor.

*   `detect_scale`: (float) Scale at which detection runs (lower is faster).
*   `learning_rate`: (float) MOG2 learning rate.
*   `mog2_var_threshold`: (float) Variance threshold for pixel classification.

### Tracker
Kalman Filter settings for object tracking.

*   `kalman`:
    *   `track_min_age`: (int) Minimum frames a track exists before being reported.
    *   `easy_iou_thresh`: (float) High IOU threshold for easy assignments.
    *   `iou_thresh`: (float) Minimum IOU for assignment.
    *   `max_lost`: (int) Max frames to keep a lost track.
    *   `min_move`: (float) Minimum pixel movement to consider a track "moving".
    *   `ema_alpha`: (float) Smoothing factor for track area.
    *   `dist_gate_scale`: (float) Gating scale for association distance.

## Usage

Run the main application using `main.py`.

```bash
python main.py --data-path /path/to/video_or_images --out-dir /path/to/results --config-path config.yaml
```

### Arguments
*   `--data-path`: Path to a video file or a directory containing images.
*   `--out-dir`: Directory where results (debug videos, logs) will be saved.
*   `--config-path`: Path to the YAML configuration file (defaults to `config.yaml`).

## Project Structure

*   `main.py`: Application entry point.
*   `config_loader.py`: Handles loading and parsing `config.yaml`.
*   `debug_utils.py`: Utilities for visualization, logging, and video writing.
*   `modules/`: Contains the core logic.
    *   `atr_vmd.py`: Main processing class coordinating Registration, Detection, and Tracking.
    *   `registrator.py`: Image registration logic.
    *   `detector.py`: Object detection logic.
    *   `kalman.py`: Kalman filter tracker.
    *   `*.cpp`: C++ implementations of the above modules.
    *   `setup_translation_gpu_cpp.py`: Build script for C++ extensions.

## Developer Notes

When extending the system, note that `ATR_VMD` (in `modules/atr_vmd.py`) acts as the facade. It initializes the appropriate implementations (Python vs C++, CPU vs GPU) based on the configuration.

If `use_cpp` and `use_cuda` are enabled, the system attempts to load the compiled `_register_detect_cpp` extension. If that fails or is not built, it gracefully falls back to the Python/OpenCV implementation (though performance may decrease).
