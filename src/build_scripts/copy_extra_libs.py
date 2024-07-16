
if __name__ == '__main__':
    import shutil
    import pathlib
    from glob import glob

    # faiss_libs = glob('.\\.venv\\Lib\\site-packages\\faiss*\\')
    ort_libs = glob('.\\.venv\\Lib\\site-packages\\onnxruntime*\\')
    sp_libs = glob('.\\.venv\\Lib\\site-packages\\sentencepiece*\\')
    tokenizer_libs = glob('.\\.venv\\Lib\\site-packages\\tokenizers*\\')

    # all_libs = faiss_libs + ort_libs + sp_libs
    all_libs = ort_libs + sp_libs + tokenizer_libs

    print('Adding libraries:')
    print(all_libs)

    tgt_loc = '.\\dist\\run_server'

    for f in all_libs:
        print(f'Copying {f}')
        f_path = pathlib.Path(f)
        shutil.copytree(f, tgt_loc + f'\\{f_path.name}', dirs_exist_ok=True)

    import os
    os.rename('.\\dist\\run_server', '.\\dist\\backend')
