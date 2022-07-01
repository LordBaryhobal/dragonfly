#!/usr/bin/env bash

export PATH=$PATH:~/.local/bin

# Get the directory the script is in
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR
sphinx-apidoc -f -o source ../src/
make html
