from distutils.core import setup
import py2exe

setup(
    options={
        'py2exe': {	
            'bundle_files': 2, 
            'optimize': 2,
        }},
    windows=[{
        "script": 'autoshares.py', 
        "includes": ['ctypes', '_ctypes'],
    }],
    zipfile = None,
)