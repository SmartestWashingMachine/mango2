cd ../../src

set SOURCE_DATE_EPOCH=0

python ../scripts/build/py/copy_extra_libs.py

python ../scripts/build/py/move_frontend.py

pause