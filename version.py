import datetime
import importlib.metadata
import inspect
import pathlib
import logging

LOGGER = logging.getLogger(__name__)
PYTOML_FILE = "pyproject.toml"

def get_version(pkg_name: str) -> str:
    """Return package version as string"""
    __version__ = None
    # print('Attempt to identify package version...')
    __version__ = _get_pytoml_version(pkg_name) 
    if not __version__:
         __version__ = _get_metadata_version(pkg_name)
    if not __version__:
        __version__ = _get_calling_module_file_version()
    if not __version__:
        __version__ = "Unknown"
    return __version__

def _get_pytoml_version(pkg_name) -> str:
    current_dir = pathlib.Path(__file__)
    toml_dir = [p for p in current_dir.parents if p.parts[-1]==pkg_name][0]
    toml_file = pathlib.Path(toml_dir) / PYTOML_FILE
    ver = None
    if toml_file.exists():
        with open(toml_file, "r") as fh_toml:
            lines = fh_toml.readlines()
        line = [ x for x in lines if "version " in x ]
        if line:
            ver = line[0].split("=")[1].strip().replace('"', '')
            
    # print(f'_get_pytoml_version: {ver}')            
    return ver

def _get_metadata_version(pkg_name: str) -> str:
    try:
        ver = importlib.metadata.version(pkg_name)
    except:
        ver = None
    
    # print(f'_get_metadata_version: {ver}')
    return ver

def _get_calling_module_file_version() -> str:
    ver = None
    frms = inspect.stack()
    frm = frms[len(frms)-1] # Lowest frame in the stack
    mod = inspect.getmodule(frm[0])
    if pathlib.Path(mod.__file__):
        base_module = pathlib.Path(mod.__file__)
        ver = datetime.datetime.fromtimestamp(base_module.stat().st_mtime)
    
    # print(f'_get_calling_module_file_version: {ver}')
    return ver

