cd ../../src

call .venv\Scripts\activate

set SOURCE_DATE_EPOCH=0

python ../scripts/build/py/move_backend_back.py

call deactivate

cd ../scripts/build

pause