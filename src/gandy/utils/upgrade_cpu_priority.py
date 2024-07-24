from gandy.utils.fancy_logger import logger

# From: https://stackoverflow.com/questions/1023038/change-process-priority-in-python-cross-platform
def upgrade_cpu_priority():
    try:
        import win32api,win32process,win32con

        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.ABOVE_NORMAL_PRIORITY_CLASS)
    except Exception as e:
        print(e)
        logger.error(e)
