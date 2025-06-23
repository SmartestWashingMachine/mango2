
if __name__ == '__main__':
    import shutil
    import os

    try:
        shutil.copytree('.\\..\js-src\\resources\\fonts', '.\\..\js-src\\dist\\win-unpacked\\resources\\fonts', dirs_exist_ok=True)
    except Exception as e:
        print('Did not copy fonts ERROR:')
        print(e)
        pass

    try:
        shutil.copytree('.\\..\src\\templates', '.\\..\js-src\\dist\\win-unpacked\\templates', dirs_exist_ok=True)
        shutil.copytree('.\\..\src\\static', '.\\..\js-src\\dist\\win-unpacked\\static', dirs_exist_ok=True)
    except Exception as e:
        print(e)
        print('--- No web ui built. Ignoring.')

    os.makedirs(".\\..\js-src\\dist\\win-unpacked\\models")

    shutil.move('.\\dist\\run_server', '.\\..\js-src\\dist\\win-unpacked\\resources\\backend')

    #os.makedirs(".\\..\js-src\\dist\\Mango", exist_ok=True)
    #shutil.move(target, ".\\..\js-src\\dist\\Mango")

    #os.makedirs(".\\..\js-src\\dist\\Mango\\models")
