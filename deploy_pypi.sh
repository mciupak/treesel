#!/usr/bin/env bash

VER=$(python -c "import treesel;print treesel.__version__")
# 1) first convert README.md markdown into README.rst
# pandoc was install from "brew install pandoc" at mac
#pandoc --from=markdown --to=rst --output=README.rst README.md

# 2) make egg and tar.gz at dist directory
python setup.py sdist

# 3) install twine
pip install twine
# twine으로 등록 후
twine register dist/treesel-$VER.tar.gz
# twine으로 파일 업로드하기
twine upload dist/treesel-$VER.tar.gz
