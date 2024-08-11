
if __name__ == '__main__':
    # Copy screenshot JS library for OCR box scanning.
    import shutil
    shutil.copytree('.\\..\js-src\\node_modules\\screenshot-desktop\\lib\\win32', '.\\..\js-src\\dist\\win-unpacked\\resources\\app.asar.unpacked\\public')
