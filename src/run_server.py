import os

os.environ['CUDA_MODULE_LOADING'] = "LAZY"

# Pyinstaller compiled apps go haywire when print() statements are called with certain unicode characters.
# See: https://groups.google.com/g/pyinstaller/c/e60IKzBqDqY
# NOTE: This still does not work. WHYYYYYYYY
os.environ["PYTHONIOENCODING"] = "utf-8"

# Partially vibe-coded below:
# Since we're using an old onnxruntime installation, we can't manually specify a preload DLL area.
# Why can't we upgrade onnxruntime? Because the fantastic people over there decided to remove support for Python 3.9 "following Numpy" (even though many people avoid the new Numpy for this exact reason).
# So here we hack the path to point to our preloaded CUDA binaries. These CUDA binaries are extracted from a local Pytorch installation I had, so they should be compatible on a wide variety of hardware (albeit much heavier than I want).
# The binaries from llama-cpp are from a newer, probably better, CUDA

# We re-use some of the DLL's from llamacpp-gpu to save on disk space :3
# Unfortunately we can't re-use the VRAM: two separate CUDA libs will be loaded into memory. SAD!
CUDA_BIN = os.path.join('models', "llamacpp_gpu")
CUDNN_BIN = CUDA_BIN

# Prepend the custom paths to the front of the PATH variable
# The .join is safer than f-strings for PATH manipulation
# os.pathsep is ';' on Windows
new_path_parts = [CUDA_BIN, CUDNN_BIN]
current_path_parts = os.environ.get('PATH', '').split(os.pathsep)

# Filter out empty strings or existing entries to keep it clean.
# Manually removing existing default CUDA installations here since they might be too old for ONNX.
# You see, ONNX is a *very* picky eater. It wants cudNN 9.x and CUDA 12.x - anything less and it just silently fails or explodes.
filtered_path = [p for p in current_path_parts if p and p not in new_path_parts and "NVIDIA" not in p]

os.environ['PATH'] = os.pathsep.join(new_path_parts + filtered_path)


# monkey.patch_all(os=True, socket=True, ssl=True, thread=True, threading=True)
#monkey.patch_os()
#monkey.patch_socket()
#monkey.patch_ssl()
# monkey.patch_thread()
# monkey.patch_queue()

import tqdm
from time import strftime
import logging

import sklearn
import sklearn.neighbors
import sklearn.tree
import sklearn.metrics._pairwise_distances_reduction._datasets_pair
import sklearn.metrics._pairwise_distances_reduction._middle_term_computer
import sklearn.metrics._pairwise_distances_reduction

import unidic_lite
from unidic_lite import unidic

import pillow_avif

from gandy.app import run_server

run_server()

# TODO: Better importing.