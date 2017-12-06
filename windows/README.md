# P.1203 Installation on Windows

First, install python3 via `python-3.6.1.exe`. Check the box so that python3 will be included in the `PATH`.

Second, install all dependencies. Open a `cmd` window, change to this folder and run the following commands:

```
pip3 install --use-wheel numpy-1.13.0+mkl-cp36-cp36m-win32.whl
pip3 install --use-wheel pandas-0.20.2-cp36-cp36m-win32.whl
pip3 install --use-wheel scipy-0.19.0-cp36-cp36m-win32.whl
```