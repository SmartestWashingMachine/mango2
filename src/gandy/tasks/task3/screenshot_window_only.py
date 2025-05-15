import numpy as np
from ctypes import windll
import win32gui
import win32ui
import re
from contextlib import contextmanager
from PIL import Image
from gandy.utils.get_scale_factor import get_windows_scale_factor, SCALE_FACTOR

# Vibe coded a lot of this. Pretty sure some of the code here is from an issue in the MSS repo.

def get_intersection(sub_box, capture_box):
    """
    Calculate the intersection of the Sub Box and Capture Box.

    Parameters:
        sub_box (tuple): Coordinates of the Sub Box (x1, y1, x2, y2).
        capture_box (tuple): Coordinates of the Capture Box (x1, y1, x2, y2).

    Returns:
        tuple: Coordinates of the intersection box (x1, y1, x2, y2),
               or None if there is no intersection.
    """
    # Extract coordinates
    sub_x1, sub_y1, sub_x2, sub_y2 = sub_box
    cap_x1, cap_y1, cap_x2, cap_y2 = capture_box

    # Calculate the intersection coordinates
    inter_x1 = max(sub_x1, cap_x1)
    inter_y1 = max(sub_y1, cap_y1)
    inter_x2 = min(sub_x2, cap_x2)
    inter_y2 = min(sub_y2, cap_y2)

    # Check if there is an intersection
    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
        return [inter_x1, inter_y1, inter_x2, inter_y2]
    else:
        return None  # No intersection


@contextmanager
def gdi_resource_management(hwnd):
    # Acquire resources
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    
    try:
        yield hwnd_dc, mfc_dc, save_dc, bitmap
    finally:
        # Ensure resources are released
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

class WindowMgr:
    def __init__(self):
        self._handle = None

    @property
    def handle(self):
        return self._handle

    def _window_enum_callback(self, hwnd, wildcard):
        if self._handle is None and re.search(wildcard, str(win32gui.GetWindowText(hwnd)), re.IGNORECASE) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)
        return self

def capture_window_image_from_box(window_name: str, box_coords, do_scale=True):
    windll.user32.SetProcessDPIAware()

    #hwnd = win32gui.FindWindow(None, window_name)
    hwnd = WindowMgr().find_window_wildcard(window_name).handle

    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bottom - top

    # Computed width/height here doesn't exactly correspond to those computed with ClientRect.
    # We use the screen left and top offsets to compute the box regions to scan.
    screen_left, screen_top, screen_right, screen_bottom = win32gui.GetWindowRect(hwnd)

    with gdi_resource_management(hwnd) as (hwnd_dc, mfc_dc, save_dc, bitmap):
        bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bitmap)

        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

        if not result:
            raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")
        
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)

    img = np.frombuffer(bmpstr, dtype=np.uint8)

    img = img.reshape((bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))
    img = np.ascontiguousarray(img)[..., :-1]  # make image C_CONTIGUOUS and drop alpha channel

    img = img[:, :, ::-1] # BGR to RGB.

    # Crop according to bounding box [x1, y1, x2, y2] AKA [left, top, right, bottom].
    img = Image.fromarray(img)

    if box_coords is not None:

        if do_scale:
            scale_factor = SCALE_FACTOR # get_windows_scale_factor()
            box_coords[0] *= scale_factor
            box_coords[1] *= scale_factor
            box_coords[2] *= scale_factor
            box_coords[3] *= scale_factor

        intersection = get_intersection([screen_left, screen_top, (screen_left + w), (screen_top + h)], box_coords)
        if intersection is None:
            raise RuntimeError('Bounding Box is not within the window.')

        # Not sure if this part is necessary.
        adjusted_left = abs(w - (screen_right - screen_left)) // 2
        adjusted_top = abs(h - (screen_bottom - screen_top)) // 2

        img = img.crop((
            intersection[0] - screen_left - adjusted_left,
            intersection[1] - screen_top - adjusted_top,
            intersection[2] - screen_left,
            intersection[3] - screen_top,
        ))

    return img
