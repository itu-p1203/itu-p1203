#!/bin/bash
# make sure that this script will be started in the correct folder
scriptPath=${0%/*}
cd "$scriptPath/../"

./setup.py build && ./setup.py install

itu-p1203 examples/mode0.json

