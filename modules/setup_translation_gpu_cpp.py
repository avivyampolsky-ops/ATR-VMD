from __future__ import annotations

# Build in-place from this directory:
#   python setup_translation_gpu_cpp.py build_ext --inplace
# Requires: pybind11 and OpenCV (with CUDA headers/libs) available in the active env.

import subprocess
import sys
import os
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from pybind11.setup_helpers import Pybind11Extension, build_ext as build_ext_pybind11

def _pkg_config_flags(package: str) -> dict:
    try:
        output = subprocess.check_output(
            ["pkg-config", "--cflags", "--libs", package],
            text=True,
        ).strip()
    except Exception:
        return {
            "include_dirs": [],
            "library_dirs": [],
            "libraries": [],
            "extra_compile_args": [],
            "extra_link_args": [],
        }

    include_dirs = []
    library_dirs = []
    libraries = []
    extra_compile_args = []
    extra_link_args = []

    for flag in output.split():
        if flag.startswith("-I"):
            include_dirs.append(flag[2:])
        elif flag.startswith("-L"):
            library_dirs.append(flag[2:])
        elif flag.startswith("-l"):
            libraries.append(flag[2:])
        else:
            extra_compile_args.append(flag)
            extra_link_args.append(flag)

    return {
        "include_dirs": include_dirs,
        "library_dirs": library_dirs,
        "libraries": libraries,
        "extra_compile_args": extra_compile_args,
        "extra_link_args": extra_link_args,
    }


opencv_flags = _pkg_config_flags("opencv4")
if not opencv_flags["include_dirs"]:
    opencv_flags = _pkg_config_flags("opencv")

# FALLBACK: Explicitly check standard locations if pkg-config fails or misses them
potential_includes = [
    "/usr/include/opencv4",
    "/usr/local/include/opencv4",
    "/usr/include",
    "/usr/local/include",
    str(Path(sys.prefix) / "include" / "opencv4")
]

for inc in potential_includes:
    if os.path.isdir(inc):
        if inc not in opencv_flags["include_dirs"]:
            print(f"Adding include path: {inc}")
            opencv_flags["include_dirs"].append(inc)

env_lib = Path(sys.prefix) / "lib"
if env_lib.exists():
    opencv_flags["library_dirs"].insert(0, str(env_lib))
    opencv_flags["extra_link_args"].append(f"-Wl,-rpath,{env_lib}")

required_opencv_libs = [
    "opencv_core",
    "opencv_imgproc",
    "opencv_video",
    "opencv_calib3d",
    "opencv_features2d",
    "opencv_flann",
    "opencv_cudaarithm",
    "opencv_cudabgsegm",
    "opencv_cudafilters",
    "opencv_cudaimgproc",
    "opencv_cudawarping",
    "opencv_xfeatures2d",
]
existing_libs = set(opencv_flags["libraries"])
for lib in required_opencv_libs:
    if lib not in existing_libs:
        opencv_flags["libraries"].append(lib)

# --- 3rdparty: CudaSift ---
cudasift_root = Path(__file__).parent / "3rdparty" / "CudaSift"
cudasift_sources = []
if cudasift_root.exists():
    opencv_flags["include_dirs"].append(str(cudasift_root))
    # Exclude match.cu and matching.cu as they contain x86 intrinsics (immintrin.h) incompatible with ARM64
    # and we only use the extraction part.
    cudasift_sources.extend([str(p) for p in cudasift_root.glob("*.cu") if "match" not in p.name])
    cudasift_sources.extend([str(p) for p in cudasift_root.glob("*.cpp") if "mainSift" not in p.name])

# --- 3rdparty: PopSift & Popcorn ---
popsift_root = Path(__file__).parent / "3rdparty" / "PopSift"
popcorn_root = Path(__file__).parent / "3rdparty" / "Popcorn"
popsift_sources = []
if popsift_root.exists() and popcorn_root.exists():
    popsift_src_dir = popsift_root / "src"
    popcorn_src_dir = popcorn_root / "src"

    opencv_flags["include_dirs"].append(str(popsift_src_dir))
    opencv_flags["include_dirs"].append(str(popcorn_src_dir))

    popsift_subdir = popsift_src_dir / "popsift"
    if popsift_subdir.exists():
        popsift_sources.extend([str(p) for p in popsift_subdir.glob("*.cu")])
        popsift_sources.extend([str(p) for p in popsift_subdir.glob("*.cpp")])

# --- Custom Build Ext to handle CUDA (.cu) files ---
class CUDA_build_ext(build_ext_pybind11):
    def build_extensions(self):
        # Check for nvcc
        try:
            subprocess.check_output(["nvcc", "--version"])
        except OSError:
            print("CUDA compiler (nvcc) not found. Building without CUDA extension support might fail if .cu files are present.")

        self.compiler.src_extensions.append(".cu")

        if hasattr(self.compiler, "_compile"):
            original_underscore_compile = self.compiler._compile

            def new_underscore_compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
                if os.path.splitext(src)[1] == ".cu":
                    # NVCC compilation
                    nvcc_args = ["-c", src, "-o", obj]
                    for inc in self.compiler.include_dirs:
                        nvcc_args.extend(["-I", inc])

                    # CudaSift flags
                    nvcc_args.extend(["-Xcompiler", "-fPIC", "-O3"])

                    # Add macros
                    for arg in extra_postargs:
                        if arg.startswith("-D"):
                            nvcc_args.append(arg)

                    # PopSift requires C++14 or newer for CUDA
                    nvcc_args.append("--std=c++14")

                    print(f"Compiling CUDA source: {' '.join(['nvcc'] + nvcc_args)}")
                    self.compiler.spawn(["nvcc"] + nvcc_args)
                    return
                return original_underscore_compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

            self.compiler._compile = new_underscore_compile

        super().build_extensions()

# Define _translation_gpu_cpp with added sources
translation_sources = [str(Path(__file__).parent / "translation_gpu_cpp.cpp")]
translation_sources.extend(cudasift_sources)
translation_sources.extend(popsift_sources)

extra_compile_args = opencv_flags["extra_compile_args"][:]
if cudasift_sources:
    extra_compile_args.append("-DENABLE_CUDASIFT")
if popsift_sources:
    extra_compile_args.append("-DENABLE_POPSIFT")

ext_modules = [
    Pybind11Extension(
        "_translation_gpu_cpp",
        translation_sources,
        include_dirs=opencv_flags["include_dirs"],
        library_dirs=opencv_flags["library_dirs"],
        libraries=opencv_flags["libraries"],
        extra_compile_args=extra_compile_args,
        extra_link_args=opencv_flags["extra_link_args"],
        cxx_std=17,
    ),
    Pybind11Extension(
        "_detector_cpp",
        [str(Path(__file__).parent / "detector_cpp.cpp")],
        include_dirs=opencv_flags["include_dirs"],
        library_dirs=opencv_flags["library_dirs"],
        libraries=opencv_flags["libraries"],
        extra_compile_args=opencv_flags["extra_compile_args"],
        extra_link_args=opencv_flags["extra_link_args"],
        cxx_std=17,
    ),
    Pybind11Extension(
        "_register_detect_cpp",
        [str(Path(__file__).parent / "register_detect_cpp.cpp")],
        include_dirs=opencv_flags["include_dirs"],
        library_dirs=opencv_flags["library_dirs"],
        libraries=opencv_flags["libraries"],
        extra_compile_args=opencv_flags["extra_compile_args"],
        extra_link_args=opencv_flags["extra_link_args"],
        cxx_std=17,
    ),
]

setup(
    name="translation_gpu_cpp",
    version="0.0.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CUDA_build_ext},
)
