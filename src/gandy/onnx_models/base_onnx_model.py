from onnxruntime import (
    GraphOptimizationLevel,
    InferenceSession,
    SessionOptions,
)
from gandy.utils.fancy_logger import logger


# If creating a model from this, make sure to manually call load_dataloader() (if needed), and load_session.
class BaseONNXModel:
    def __init__(self, use_cuda):
        self.use_cuda = use_cuda

    def forward(self, x):
        pass

    def load_dataloader(self):
        """
        The dataloader is used to preprocess the given raw input (inp) into the processed input (x).
        """
        pass

    def create_session(self, onnx_path):
        if self.use_cuda is None:
            raise RuntimeError("use_cuda must be True or False.")

        options = SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        # options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL

        options.enable_mem_pattern = False
        options.enable_profiling = False
        options.enable_cpu_mem_arena = False
        options.enable_mem_reuse = False
        cuda_provider_options = {"arena_extend_strategy": "kSameAsRequested", "do_copy_in_default_stream": False, "cudnn_conv_use_max_workspace": "0"}

        options.log_severity_level = 3

        # Note that CUDA errors are not properly logged right now :/
        if self.use_cuda:
            logger.info("CUDA enabled. Will try to use CUDA if allowed.")
            provider = [("CUDAExecutionProvider", cuda_provider_options), "CPUExecutionProvider"]
        else:
            logger.info("CUDA disabled. Will only use CPU.")
            provider = ["CPUExecutionProvider"]

        self.ort_sess = InferenceSession(onnx_path, options, provider)
        # ? self.ort_sess.disable_fallback()

        return self.ort_sess

    def load_session(self, onnx_path):
        self.ort_sess = self.create_session(onnx_path)

    def preprocess(self, inp):
        """
        Process the input into a form of data that can be passed to .forward().
        """
        return inp

    def postprocess(self, y_hat):
        return y_hat

    def begin_forward(self, x, *args, **kwargs):
        return self.forward(x, *args, **kwargs)

    def full_pipe(self, inp, *forward_args, **forward_kwargs):
        """
        Given a raw input, fully process it and return the proper output.
        """

        x = self.preprocess(inp)
        return self.postprocess(self.begin_forward(x, *forward_args, **forward_kwargs))

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
