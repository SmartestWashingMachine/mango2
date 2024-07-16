from gandy.onnx_models.base_onnx_model import BaseONNXModel


class YOLOONNX(BaseONNXModel):
    def __init__(self, onnx_path, use_cuda):
        super().__init__(use_cuda=use_cuda)

        self.load_session(onnx_path)

    def forward(self, x):
        input_name = self.ort_sess.get_inputs()[0].name

        ort_inputs = {
            input_name: x,
        }
        ort_outs = self.ort_sess.run(None, ort_inputs)

        return ort_outs[0]  # bboxes
