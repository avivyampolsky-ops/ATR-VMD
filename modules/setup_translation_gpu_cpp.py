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
env_include = Path(sys.prefix) / "include" / "opencv4"
if env_include.exists():
    opencv_flags["include_dirs"].insert(0, str(env_include))
if "/usr/include/opencv4" not in opencv_flags["include_dirs"]:
    if Path("/usr/include/opencv4/opencv2/core.hpp").exists():
        opencv_flags["include_dirs"].append("/usr/include/opencv4")
env_lib = Path(sys.prefix) / "lib"
if env_lib.exists():
    opencv_flags["library_dirs"].insert(0, str(env_lib))
    opencv_flags["extra_link_args"].append(f"-Wl,-rpath,{env_lib}")

if env_include.exists():
    opencv_flags["include_dirs"] = [
        d for d in opencv_flags["include_dirs"]
        if d not in ("/usr/include/opencv4", "/usr/local/include/opencv4")
    ]

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
    cudasift_sources.extend([str(p) for p in cudasift_root.glob("*.cu")])
    cudasift_sources.extend([str(p) for p in cudasift_root.glob("*.cpp") if "mainSift" not in p.name])

# --- Custom Build Ext to handle CUDA (.cu) files ---
class CUDA_build_ext(build_ext_pybind11):
    def build_extensions(self):
        # Check for nvcc
        try:
            subprocess.check_output(["nvcc", "--version"])
        except OSError:
            print("CUDA compiler (nvcc) not found. Building without CUDA extension support might fail if .cu files are present.")

        # We need to separate compilation of .cu files
        self.compiler.src_extensions.append(".cu")

        # Save original compile method
        original_compile = self.compiler.compile

        def unix_compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
            # For .cu files, use nvcc
            if os.path.splitext(src)[1] == ".cu":
                self.compiler.set_executable("compiler_so", "nvcc")

                # Filter flags for nvcc
                postargs = [
                    "-c",
                    "-Xcompiler", "-fPIC", # Pass fPIC to host compiler
                    "-O3"
                ]
                # Add include dirs
                for inc in self.compiler.include_dirs:
                    postargs.append(f"-I{inc}")

                # Add macros
                # (Assuming pp_opts usually contains macros/defs, but distutils is messy.
                #  We will trust extra_postargs or add basic ones)

                # Compile
                try:
                    self.compiler.spawn(["nvcc", src] + postargs + ["-o", obj])
                except Exception as e:
                    raise RuntimeError(f"Error compiling {src} with nvcc: {e}")
                return

            # For other files, use original compiler (gcc/g++)
            self.compiler.set_executable("compiler_so", "c++") # Enforce C++
            return original_compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

        # Monkey patch (a bit hacky but common for simple mixed builds)
        # Better way: override _compile in UnixCCompiler
        # But `compile` is the high level entry.
        # Let's try to just intercept specific calls if possible, or use standard override.

        # Actually, simpler approach for `build_ext`: iterate extensions and compile sources manually?
        # No, let's use the provided hook.

        # NOTE: self.compiler is initialized in `build_extensions`.
        # But overriding `compile` is method-bound.
        # Let's override the compiler's `_compile` method if it's a UnixCCompiler

        if hasattr(self.compiler, "_compile"):
            original_underscore_compile = self.compiler._compile

            def new_underscore_compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
                if os.path.splitext(src)[1] == ".cu":
                    # NVCC compilation
                    nvcc_args = ["-c", src, "-o", obj]
                    # Includes
                    for inc in self.compiler.include_dirs:
                        nvcc_args.extend(["-I", inc])
                    # Macros?
                    # cflags?
                    nvcc_args.extend(["-Xcompiler", "-fPIC", "-O3"])

                    # Add -DENABLE_CUDASIFT if needed (it is passed in extra_compile_args usually)
                    for arg in extra_postargs:
                        if arg.startswith("-D"):
                            nvcc_args.append(arg)

                    print(f"Compiling CUDA source: {' '.join(['nvcc'] + nvcc_args)}")
                    self.compiler.spawn(["nvcc"] + nvcc_args)
                    return
                return original_underscore_compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

            self.compiler._compile = new_underscore_compile

        super().build_extensions()

# Define _translation_gpu_cpp with added sources
translation_sources = [str(Path(__file__).parent / "translation_gpu_cpp.cpp")]
translation_sources.extend(cudasift_sources)

extra_compile_args = opencv_flags["extra_compile_args"][:]
if cudasift_sources:
    extra_compile_args.append("-DENABLE_CUDASIFT")

# Note: We must NOT pass .cu files to the C++ compiler via extra_compile_args or similar.
# The custom build_ext handles them.

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
