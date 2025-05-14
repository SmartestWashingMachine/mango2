import ctypes

def get_windows_scale_factor():
    try:
        awareness = ctypes.c_int()
        errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        if errorCode == 0:
            if awareness.value == 0:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)

            hDC = ctypes.windll.user32.GetDC(0)
            horizontal_dpi = ctypes.windll.gdi32.GetDeviceCaps(hDC, 88)
            ctypes.windll.user32.ReleaseDC(0, hDC)
            return horizontal_dpi / 96
        else:
            return 1.0
    except AttributeError:
        return 1.0

SCALE_FACTOR = get_windows_scale_factor()