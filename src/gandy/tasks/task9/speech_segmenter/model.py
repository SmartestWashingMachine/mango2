# NOTE: This is from Silero VAD; adapted to use ONNX.

from .utils_vad import OnnxWrapper


def load_silero_vad(onnx=True, opset_version=16, onnx_force_cpu=True):
    """Load Silero VAD ONNX model.

    Parameters
    ----------
    onnx : bool (default True)
        Kept for API compatibility. Must be True.
    opset_version : int (default 16)
        ONNX opset version. Available: 15, 16.
    onnx_force_cpu : bool (default True)
        Force CPU execution provider.
    """
    if not onnx:
        raise ValueError("Only ONNX models are supported. Set onnx=True.")

    available_ops = [15, 16]
    if opset_version not in available_ops:
        raise ValueError(f'Available ONNX opset_version: {available_ops}')

    if opset_version == 16:
        model_name = 'silero_vad.onnx'
    else:
        model_name = f'silero_vad_16k_op{opset_version}.onnx'

    package_path = "silero_vad.data"

    try:
        from importlib.resources import files
        model_file_path = str(files(package_path).joinpath(model_name))
    except (ImportError, TypeError):
        import importlib_resources
        model_file_path = str(importlib_resources.files(package_path).joinpath(model_name))

    return OnnxWrapper(model_file_path, force_onnx_cpu=onnx_force_cpu)


def load_silero_vad_from_path(path, onnx_force_cpu=True):
    """Load Silero VAD ONNX model from an arbitrary file path.

    Parameters
    ----------
    path : str
        Path to an ONNX model file.
    onnx_force_cpu : bool (default True)
        Force CPU execution provider.
    """
    return OnnxWrapper(str(path), force_onnx_cpu=onnx_force_cpu)
