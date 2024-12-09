# FeatureReplacement Introduction
This program is designed for use in research and data sharing. It loads a video of a person performing a motor exercise and outputs an annonymized video. 

The video is annonymied using DeepFake AI, swapping the facial features of the original person with the features of a fake AI generated person. Recognizable features are in this way removed, but the the facial expressions and mimicry relevant for research is preserved. 

# Installing the program on macOS (Sonoma 14.5(23F79))
## Install Homebrew
```
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Or install it with .pkg file though following link: https://github.com/Homebrew/brew/releases/latest


## Install python packages through Homebrew
```
$ brew install pyinstaller
$ brew install opencv
$ brew install matplotlib
$ brew install python-tk@3.12
```

## Install python pip packages that does not exist in Homebrew into the Homebrew environment 
```
$ python -m pip install insightface --break-system-packages
$ python -m pip install onnxruntime --break-system-packages
$ python -m pip install moviepy --break-system-packages
$ python -m pip install PythonVideoConverter --break-system-packages
$ python -m pip install customtkinter --break-system-packages
$ python -m pip install tkinter --break-system-packages

```

## Make python3 refer to Homebrew python
start by finding the right for homebrew
```
brew info python
```
gives the following output: 
```
Unversioned symlinks `python`, `python-config`, `pip` etc. pointing to
`python3`, `python3-config`, `pip3` etc., respectively, have been installed into
  /opt/homebrew/opt/python@3.12/libexec/bin
```
Now export to that path
```
$ echo 'export PATH=/opt/homebrew/opt/python@3.9/libexec/bin:$PATH' >> ~/.zprofile
$ source ~/.zprofile
```

## Make sure that you have the following files
`./Files/inswapper_128.onnx`
`./Files/SourceImages/source-image.png`
`./target-video.mp4`
`./feature-replacement.py`


## Check if the program runs
´´´
$ python3 feature-replacement.py 
´´´


## Transform it into .exe file 
First install pyinstaller
```
$ sudo -i         
```
(apparently you have to be root in order to install it correctly)
```
$ brew install pyinstaller
```

Now create the .spec file 
```
$ pyinstaller --clean -y -n "feature-replacement" --add-data="Files/.":"Files" feature-replacement.py -w
```

This creates .exe file and .spec file. If you try to run the .exe file now you will probably have problems with the `insightface` and `wx` libraries. These liraries need to be added to the .spec file. You can find the path to the libraries adding this to your python code `print(sys.path)`

The start of the file looks like this
```
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['feature-replacement.py'],
    pathex=[],
    binaries=[],
    datas=[('Files/.', 'Files')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
######### Following part is what needs to be added #############
a.datas += Tree("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/insightface", prefix="insightface")
#########  Previous part is what needs to be added  #############

...
```
To reference the embedded folder in python write the following: 
```
if getattr(sys, 'frozen', False):    # Evaluates only to True if the program is run as .exe
    file_path = os.path.join(sys._MEIPASS, "Files/fileThatINeed.txt)
else:
    file_path = os.path.join("./Files/fileThatINeed.txt)
```

Now with the libraries added create the .exe file using the .spec file. 
```
$ pyinstaller feature-replacement.spec --noconfirm
```
