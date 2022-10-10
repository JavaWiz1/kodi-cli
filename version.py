import datetime
import importlib.metadata
import inspect
import pathlib
import logging
import platform

LOGGER = logging.getLogger("Version")
PYTOML_FILE = "pyproject.toml"

def get_version(pkg_name: str) -> str:
    """
    Return package version as string.
    Determines in following order:
    - pytoml file (if exists)
    - version from package metadata
    - module last modified date/time
    """
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
    """Retrieve version string from pytoml file"""
    current_dir = pathlib.Path(__file__)
    # traverse up directory tree looking for pyproject.toml
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
    """Retrieve version from package metadata"""
    try:
        ver = importlib.metadata.version(pkg_name)
    except:
        ver = None
    
    # print(f'_get_metadata_version: {ver}')
    return ver

def _get_calling_module_file_version() -> str:
    """Retrieve version based on last modified timestamp from calling module file"""
    ver = None
    frms = inspect.stack()
    frm = frms[len(frms)-1] # Lowest frame in the stack
    mod = inspect.getmodule(frm[0])
    if pathlib.Path(mod.__file__):
        base_module = pathlib.Path(mod.__file__)
        ver = datetime.datetime.fromtimestamp(base_module.stat().st_mtime)
    
    # print(f'_get_calling_module_file_version: {ver}')
    return ver


def get_host_info() -> dict:
    """
    Return dictionary of host info:
    - name
    - Processor
    - OS Release, Type and Version
    - Python version
    """
    host_info = {}
    host_info['Hostname'] = platform.node()
    host_info['Processor'] = platform.processor()
    host_info['Release'] = platform.release()
    host_info['OS Type'] = platform.system()
    host_info['OS Version'] = platform.version()
    host_info['Python'] = platform.python_version()
    return host_info
