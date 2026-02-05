
import time
import cv2
import numpy as np
import argparse
from modules.atr_vmd import ATR_VMD
from config_loader import ConfigLoader
from modules.features import FeatureExtractorType

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="data/test_image.jpg", help="Path to a test image")
    args = parser.parse_args()

    # Create dummy image if not exists
    img = None
    if args.image:
        img = cv2.imread(args.image)

    if img is None:
        print("Image not found or not provided, generating random noise image (1920x1080)...")
        img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    # Base config
    config_path = "config.yaml"
    # Create a dummy config loader that we can patch
    class MockConfig:
        def __init__(self):
            self.data = {
                "general": {"use_cpp": True, "use_cuda": True, "input_is_gray": False},
                "registration": {
                    "mode": "homography",
                    "downscale_factor": 1.0,
                    "reference_window_ms": 500.0,
                    "homography": {
                        "feature_extractor": "SIFT",
                        "matcher": "BF",
                        "knn_ratio": 0.7,
                        "ransac_reproj_threshold": 5.0,
                        "min_inliers": 10
                    }
                },
                "detection": {"detect_scale": 1.0, "learning_rate": 0.1, "mog2_var_threshold": 25},
                "debug": {"debug_mode": False, "enable_timing": True}
            }
            self.runtime = {}

        def get(self, key, default=None):
            if key in self.runtime: return self.runtime[key]
            parts = key.split(".")
            curr = self.data
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    return default
            return curr

        def feature_extractor(self):
            val = self.get("registration.homography.feature_extractor")
            if val == "CUDA_SIFT": return FeatureExtractorType.CUDA_SIFT
            if val == "POP_SIFT": return FeatureExtractorType.POP_SIFT
            return FeatureExtractorType.SIFT

        def matcher(self):
            return "BF" # Simplified

    # Test Configurations
    configs = [
        ("OpenCV SIFT (CPU)", "SIFT"),
        ("CudaSift (GPU)", "CUDA_SIFT"),
        # ("PopSift (GPU)", "POP_SIFT") # Disabled until built
    ]

    print(f"Testing SIFT Performance on Image: {img.shape}")

    for name, extractor in configs:
        print(f"\n--- Testing {name} ---")
        cfg = MockConfig()
        cfg.data["registration"]["homography"]["feature_extractor"] = extractor

        try:
            # Initialize Tracker/Registrator
            # We construct ATR_VMD but mostly care about registrator
            atr = ATR_VMD(img, cfg)

            # Warmup
            print("  Warmup...")
            atr.process_frame(img)

            # Benchmark
            print("  Benchmarking 10 frames...")
            start = time.perf_counter()
            for _ in range(10):
                atr.process_frame(img) # Registers against itself (or prev ref)
            end = time.perf_counter()

            avg_ms = ((end - start) / 10.0) * 1000.0
            print(f"  Result: {avg_ms:.2f} ms/frame")

            # Check if it actually used the right one?
            # Hard to verify from python without inspecting C++ logs, but if it ran, it worked.

        except Exception as e:
            print(f"  Failed: {e}")
            if "C++ GPU homography module is not available" in str(e):
                print("  (Did you build the extensions with setup_translation_gpu_cpp.py?)")

if __name__ == "__main__":
    main()
