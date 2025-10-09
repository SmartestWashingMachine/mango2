
# THANK YOU PYINSTALLER THANK YOU PYINSTALLER THANK YOU PYINSTALLER
def try_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except:
        print("Failed to print something.")