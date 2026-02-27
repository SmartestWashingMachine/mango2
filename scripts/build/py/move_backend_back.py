
if __name__ == '__main__':
    import shutil
    import os

    # build_js clears the build folder - let's move the model binaries somewhere safer so they don't get deleted.
    models_folder = '.\\..\js-src\\dist\\win-unpacked\\models'
    if os.path.exists(models_folder):
        print('Model binaries exists in built app - moving to models_tmp!')
        shutil.move(models_folder, '.\\..\\models_tmp')

    # To take advantage of Pyinstaller caching for faster build-times (build_py).
    backend_folder = '.\\..\js-src\\dist\\win-unpacked\\resources\\backend'
    if os.path.exists(backend_folder):
        shutil.move(backend_folder, '.\\dist\\run_server')

    print('Done moving backend back!')
