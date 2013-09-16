from distutils.core import setup
import py2exe
from glob import glob
import sys

sys.path.append(r'C:\Program Files (x86)\Dropbox\Microsoft.VC90.CRT')

data_files = [("Microsoft.VC90.CRT", glob(r'C:\Program Files (x86)\Dropbox\Microsoft.VC90.CRT\*.*'))]
setup(
    data_files=data_files,
    windows=['main.py'],
    zipfile=None,
    options={
                "py2exe":{
                        "optimize": 2,
                        "excludes": ['_ssl', 'calendar', 'numpy',
                                     '_hashlib', '_tkinter', 'doctest', 'pdb',
                                     'inspect', 'email'],
                        "dist_dir": "converter"
                }
        }
)
