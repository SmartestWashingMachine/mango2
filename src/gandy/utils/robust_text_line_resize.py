import numpy as np
import albumentations as A
import cv2

# Some of this was vibe-coded. Having to manually design small variations of this pipeline ~10 times was killing me.

MAX_IMAGE_SIDE_LENGTH = 512


class ConditionalLongestMaxSize(A.DualTransform):
    def __init__(self, default_max_size=512,
                fallback_max_sizes=[768, 1024], # Options for larger max_size
                min_short_side_threshold=32,   # If shortest side would be <= this, use a fallback
                interpolation=cv2.INTER_LINEAR,
                p=1.0):
        
        super().__init__(p=p)
        self.default_max_size = default_max_size
        self.fallback_max_sizes = sorted(fallback_max_sizes) # Ensure sorted for picking
        self.min_short_side_threshold = min_short_side_threshold
        self.interpolation = interpolation

    @property
    def targets_as_params(self):
        # This tells Albumentations to calculate parameters once based on the image
        # and then pass those same parameters to apply_to_mask, apply_to_bbox, etc.
        return ["image"]

    def get_params_dependent_on_targets(self, params):
        img = params["image"]
        h, w = img.shape[:2]

        # Calculate what the shortest side would be if default_max_size was applied
        if h > w: # Portrait or square
            # If default_max_size is applied to height, width becomes w * (default_max_size / h)
            potential_short_side = w * (self.default_max_size / h)
        else: # Landscape or square
            # If default_max_size is applied to width, height becomes h * (default_max_size / w)
            potential_short_side = h * (self.default_max_size / w)

        selected_max_size = self.default_max_size
        
        # Check if the potential shortest side is too small
        if potential_short_side <= self.min_short_side_threshold:
            # Iterate through fallback sizes to find the smallest one that works
            for fallback_size in self.fallback_max_sizes:
                if h > w:
                    potential_new_short_side = w * (fallback_size / h)
                else:
                    potential_new_short_side = h * (fallback_size / w)
                
                if potential_new_short_side > self.min_short_side_threshold:
                    selected_max_size = fallback_size
                    break # Found a suitable fallback, stop
            else: # If loop completes without break, no fallback solved it, stick to largest fallback
                selected_max_size = self.fallback_max_sizes[-1] if self.fallback_max_sizes else self.default_max_size

        # Log the decision (optional, but good for debugging)
        #print(f"Original HxW: {h}x{w}, Aspect Ratio: {h/w:.2f}")
        #print(f"Potential shortest side with {self.default_max_size}: {potential_short_side:.2f}")
        #print(f"Selected max_size for this image: {selected_max_size}")

        return {"max_size": selected_max_size, "interpolation": self.interpolation}

    def apply(self, img, max_size=None, interpolation=cv2.INTER_LINEAR, **params):
        if max_size is None:
            raise ValueError("max_size must be provided by get_params_dependent_on_data")
        
        # Reuse Albumentations' LongestMaxSize logic
        h, w = img.shape[:2]
        if h > w: # Portrait or square
            scale = max_size / h
        else: # Landscape or square
            scale = max_size / w
        
        new_h, new_w = int(h * scale), int(w * scale)
        
        return cv2.resize(img, (new_w, new_h), interpolation=interpolation)

    def apply_to_mask(self, mask, max_size=None, interpolation=cv2.INTER_NEAREST, **params):
        # Masks should use INTER_NEAREST for interpolation
        return self.apply(mask, max_size=max_size, interpolation=interpolation)

    def apply_to_bboxes(self, bboxes, max_size=None, rows=0, cols=0, **params):
        # We need the original rows and cols to correctly scale bounding boxes
        # Store original image dimensions in get_params_dependent_on_data and pass them
        h_orig, w_orig = rows, cols
        
        if h_orig == 0 or w_orig == 0:
            return bboxes # Should not happen with valid images

        if h_orig > w_orig:
            scale = max_size / h_orig
        else:
            scale = max_size / w_orig

        # Apply scaling to each bbox coordinate (x_min, y_min, x_max, y_max)
        scaled_bboxes = []
        for bbox in bboxes:
            x_min, y_min, x_max, y_max, *rest = bbox
            scaled_bboxes.append([
                x_min * scale,
                y_min * scale,
                x_max * scale,
                y_max * scale,
                *rest
            ])
        return scaled_bboxes

    # This method defines which arguments from __init__ need to be serialized/deserialized
    # It helps with A.ReplayCompose and saving/loading transforms.
    def get_transform_init_args_names(self):
        return ("default_max_size", "fallback_max_sizes", "min_short_side_threshold", "interpolation")

robust_transform = A.Compose(
    [
        ConditionalLongestMaxSize(default_max_size=512, fallback_max_sizes=[768, 1024], p=1, min_short_side_threshold=64, interpolation=cv2.INTER_LINEAR),
        # 5. --- Final Pad to Divisible by 16 ---
        # This pads the image to meet the model's divisibility requirements.
        A.PadIfNeeded(
            min_height=None, # No fixed min height
            min_width=None,  # No fixed min width
            pad_width_divisor=16,
            pad_height_divisor=16,
            border_mode=cv2.BORDER_CONSTANT,
            value=0, # Background color
            p=1 # Always apply
        ),
        A.ToGray(p=1.0),
    ]
)
