from gandy.text_detection.base_image_detection import BaseImageDetection


class NoneImageDetectionApp(BaseImageDetection):
    def __init__(self):
        """
        This app uses a custom DETR (pretrained with resnet50, finetuned on a custom dataset).

        Why the "G" at the end? The default IoU loss was replaced with the complete IoU loss (combining IoU, distance, as well as aspect ratio differences) when finetuned.
        """
        super().__init__()

    def process(self, image):
        image_width, image_height = image.size

        speech_bboxes = [[0, 0, image_width, image_height]]
        return speech_bboxes

    def unload_model(self):
        pass
