
if __name__ == '__main__':
    import shutil

    shutil.move('.\\dist\\backend', '.\\..\js-src\\dist\\win-unpacked\\resources\\backend')

    shutil.copytree('.\\..\js-src\\resources\\fonts', '.\\..\js-src\\dist\\win-unpacked\\resources\\fonts')

    try:
        shutil.copytree('.\\..\src\\templates', '.\\..\js-src\\dist\\win-unpacked\\templates')
        shutil.copytree('.\\..\src\\static', '.\\..\js-src\\dist\\win-unpacked\\static')
    except Exception as e:
        print(e)
        print('--- No web ui built. Ignoring.')

    import os
    import shutil

    target = ".\\..\js-src\\dist\\win-unpacked"
    os.makedirs(".\\..\js-src\\dist\\win-unpacked\\models")

    #os.makedirs(".\\..\js-src\\dist\\Mango", exist_ok=True)
    #shutil.move(target, ".\\..\js-src\\dist\\Mango")

    #os.makedirs(".\\..\js-src\\dist\\Mango\\models")
