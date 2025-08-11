cd src

call .venv\Scripts\activate

set SOURCE_DATE_EPOCH=0

pyinstaller run_server.spec

cd ..

pause