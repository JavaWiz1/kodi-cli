import configparser
import pathlib
import platform
import sys
from datetime import datetime as dt
from importlib.metadata import version
from typing import List, Tuple

from loguru import logger as LOGGER

PACKAGE_NAME = "kodi_cli"


# -- Version routines ----------------------------------------------------------------------------------
def get_version() -> str:
    try:
        ver = version(PACKAGE_NAME)
    except Exception as ex:
        ver = None
        LOGGER.debug(f'Unable to retrieve version from package name [{PACKAGE_NAME}]')
        LOGGER.debug(f'Error: {ex}')
        
    if ver is None:
        toml = pathlib.Path(resolve_config_location('pyproject.toml'))
        if toml.exists():
            toml_list = toml.read_text().splitlines()
            token = [ x for x in toml_list if x.startswith('version') ]
            if len(token) == 1:
                ver = token[0].replace('version','' ).replace('=','').replace('"','').strip()
    if ver is None:
        ver = _get_version_from_mod_time()

    return ver    

def _get_version_from_mod_time() -> str:
    # version based on the mod timestamp of the most current updated python code file
    file_list = list(pathlib.Path(__file__).parent.glob("**/*.py"))
    ver_date = dt(2000,1,1,0,0,0,0)
    for file_nm in file_list:
        ver_date = max(ver_date, dt.fromtimestamp(file_nm.stat().st_mtime))
    ver = f'{ver_date.year}.{ver_date.month}.{ver_date.day}'
    return ver

def resolve_config_location(file_name: str) -> str:
    LOGGER.trace(f'Attempting to resolve location for: {file_name}')
    found_location = file_name
    first_prefix = pathlib.Path(file_name).parent
    config_prefixes = [first_prefix, './config', '../config', '.', '..', f'~/.{PACKAGE_NAME}']
    for prefix in config_prefixes:
        file_loc = pathlib.Path(f'{prefix}/{file_name}').expanduser().absolute()
        LOGGER.trace(f'- {file_loc}')
        if file_loc.exists():
            found_location = str(file_loc.absolute())
            LOGGER.trace(f'  - FOUND: {found_location}')
            break
    # Default to found location (or last entry i.e. ~/.kodi_cli/kodi_.cfg)
    found_location = file_loc.absolute()
    return found_location

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

# -- Config file routines ------------------------------------------------------------------------------
def _get_section_desc(key: str) -> Tuple[str, str]:
    entry = _KEYWORD_SECTIONS.get(key, None)
    if entry is None:
        raise KeyError(f"'{key}' does NOT exist in _KEYWORD_SECTIONS")

    section = entry['section']
    desc = entry['desc'] 
    return section, desc

def _config_notes_block() -> List[str]:
    notes = []
    notes.append(f'# {"="*80}\n')
    notes.append(f'# {PACKAGE_NAME} configuration file (auto-generated)\n')
    notes.append(f'# {"-"*80}\n')
    notes.append('# NOTES:\n')
    for keyword in _KEYWORD_SECTIONS.keys():
        section, desc = _get_section_desc(keyword)
        if len(desc) > 0:
            notes.append(f'# - {keyword:25} : {desc}\n')
    notes.append(f'# {"-"*80}\n')

    return notes

def create_template_config(overwrite: bool = False):
    this_module = sys.modules[__name__]
    filename = pathlib.Path(resolve_config_location(f'{PACKAGE_NAME}.cfg')).absolute()
    # filename = pathlib.Path(f'./config/{PACKAGE_NAME}.cfg').absolute()
    LOGGER.trace(f'Config location identified as: {filename}')
    if not filename.parent.exists():  
        LOGGER.info(f'Creating directory: {filename.parent}')
        filename.parent.mkdir()
    if filename.exists():
        if not overwrite:
            raise FileExistsError(f'{filename}, to overwrite, use -CO option')
        
    new_config = configparser.ConfigParser()
    for keyword in _KEYWORD_SECTIONS.keys():
        section, _ = _get_section_desc(keyword)
        if not new_config.has_section(section):
            new_config[section] = {}
        val =  getattr(this_module, keyword, 'TBD')
        new_config[section][keyword] = str(val)

    notes = _config_notes_block()
    with open(filename, 'w',) as h_file:
        for line in notes:
            h_file.write(line)
        new_config.write(h_file)

    LOGGER.info('')
    LOGGER.info(f'Config file [{filename}] created/updated.')
    LOGGER.info(' - Values are current settings (or default setting if not defined)')
    if '_NEW' in str(filename):
        LOGGER.warning(' - You must rename the file (to kodi_cli.cfg) for changes to take effect')
    LOGGER.info('')


# == Logger Setup ========================================================================
def configure_logger(log_target = sys.stderr, log_level: str = "INFO", log_format: str = None, log_handle: int = 0, **kwargs) -> int:
    """
    Configure logger via loguru.
     - should be done once for each logger (console, file,..)
     - if reconfiguring a logger, pass the log_handle
    
    Parameters:
        log_target: defaults to stderr, but can supply filename as well
        log_level : TRACE|DEBUG|INFO(dflt)|ERROR|CRITICAL
        log_format: format for output log line
        log_handle: handle of log being re-initialized.
        other     : keyword args related to loguru logger.add() function
    Returns:
        logger_handle_id: integer representing logger handle
    """
    try:
        LOGGER.remove(log_handle)
    except Exception as ex:
        LOGGER.trace(f'Unable to remove log handle: {log_handle}  [{ex}]')
    
    if not log_format:
        if isinstance(log_target, str):
            log_format = DEFAULT_FILE_LOGFMT
        else:
            log_format = DEFAULT_CONSOLE_LOGFMT

    hndl = LOGGER.add(sink=log_target, level=log_level, format=log_format, **kwargs)

    return hndl

    
# == Config Settings =====================================================================
FILE_CONFIG = resolve_config_location(f'{PACKAGE_NAME}.cfg')

CONFIG_EXISTS = pathlib.Path(FILE_CONFIG).exists()
_CONFIG = configparser.ConfigParser()
_CONFIG.read(FILE_CONFIG)

# ===================================================================================================================
_KEYWORD_SECTIONS = {
    "logging_enabled":      {"section": "LOGGING", "desc": "Turn on/off file logging"},
    "logging_filename":     {"section": "LOGGING", "desc": ""},
    "logging_rotation":     {"section": "LOGGING", "desc": "Limit on log file size (i.e. '15 mb')"},
    "logging_retention":    {"section": "LOGGING", "desc": "How many copies to retain (i.e. 3)"},
    "logging_level":        {"section": "LOGGING", "desc": "Log level (ERROR, WARNING, INFO, DEBUG, TRACE)"},
    "logger_blacklist":     {"section": "LOGGING", "desc": "Comma seperated list of Loggers to disable"},

    "host":                 {"section": "SERVER", "desc": "Target Kodi Host"},
    "port":                 {"section": "SERVER", "desc": "Kodi service listening port"},
    "kodi_user":            {"section": "LOGIN",  "desc": "Kodi username"},
    "kodi_pw":              {"section": "LOGIN",  "desc": "Kodi password"},
    "format_output":        {"section": "OUTPUT", "desc": "Output in JSON readable format"},
    "csv_output":           {"section": "OUTPUT", "desc": "Output in CSV format"},
}

# ===================================================================================================================
__version__ = get_version()

DEFAULT_FILE_LOGFMT = "<green>{time:MM/DD/YY HH:mm:ss}</green> |<level>{level: <8}</level>|<cyan>{name:12}</cyan>|<cyan>{line:3}</cyan>| <level>{message}</level>"
DEFAULT_CONSOLE_LOGFMT = "<level>{message}</level>"
DEBUG_CONSOLE_LOGFMT = "[<level>{level: <8}</level>] <cyan>{name:15}</cyan>[<cyan>{line:3}</cyan>] <level>{message}</level>"

logging_enabled: str    = _CONFIG.getboolean(_get_section_desc('logging_enabled')[0], 'logging_enabled', fallback=False)
_default_log_name = resolve_config_location(f'{PACKAGE_NAME}.log')
logging_filename: str   = _CONFIG.get(_get_section_desc('logging_filename')[0],       'logging_filename', fallback=_default_log_name)
logging_rotation: str   = _CONFIG.get(_get_section_desc('logging_rotation')[0],       'logging_rotation', fallback='1 MB')
logging_retention: int  = _CONFIG.getint(_get_section_desc('logging_retention')[0],   'logging_retention', fallback=3)
logging_level: str      = _CONFIG.get(_get_section_desc('logging_level')[0],          'logging_level',    fallback='INFO')
logger_blacklist: str   = _CONFIG.get(_get_section_desc('logger_blacklist')[0],       'logger_blacklist', fallback='')

host: str               = _CONFIG.get(_get_section_desc('host')[0], 'host', fallback='localhost')
port: int               = _CONFIG.getint(_get_section_desc('port')[0], 'port', fallback=8080)

kodi_user: str          = _CONFIG.get(_get_section_desc('kodi_user')[0], 'kodi_user', fallback='kodi')
kodi_pw: str            =_CONFIG.get(_get_section_desc('kodi_pw')[0], 'kodi_pw', fallback='kodi')

format_output: bool     =_CONFIG.getboolean(_get_section_desc('format_output')[0], 'format_output', fallback=False)
csv_output: bool        =_CONFIG.getboolean(_get_section_desc('csv_output')[0],    'csv_output', fallback=False)
_json_rpc_loc: str      = _CONFIG.get(section='SERVER', option='_json_rpc_loc', fallback='./json-defs')
