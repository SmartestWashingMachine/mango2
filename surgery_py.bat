cd src

set SOURCE_DATE_EPOCH=0

python build_scripts/copy_extra_libs.py

python build_scripts/move_frontend.py

pause