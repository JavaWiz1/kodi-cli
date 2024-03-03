import argparse
import os
import pathlib
import sys
import textwrap
from typing import Tuple

from loguru import logger as LOGGER

import cfg
import kodi_common as util
import kodi_output_factory as output_factory
from kodi_interface import KodiObj

# CSV_CAPABLE_COMMANDS =  {
#     'Addons.GetAddons': 'addons',
#     'AudioLibrary.GetAlbums': 'albums',
#     'AudioLibrary.GetArtists': 'artists',
#     'AudioLibrary.GetGenres': 'genres',
#     'AudioLibrary.GetRecentlyAddedAlbums': 'albums',
#     'AudioLibrary.GetRecentlyAddedSongs': 'songs',
#     'AudioLibrary.GetRecentlyPlayedAlbums': 'albums',
#     'AudioLibrary.GetRecentlyPlayedSongs': 'songs',
#     'VideoLibrary.GetRecentlyAddedEpisodes': 'episodes' 
#     }
    

__version__ = cfg.get_version()

# # === Validation routines =================================================
# def is_integer(token: str) -> bool:
#     """Return true if string is an integer"""
#     is_int = True
#     try:
#         int(token)
#     except ValueError:
#         is_int = False
#     return is_int

# def is_boolean(token: str) -> bool:
#     """Return true if string is a boolean"""
#     is_bool_str = False
#     if token in ["True", "true", "False", "false"]:
#         is_bool_str = True
#     LOGGER.debug(f'  is_boolean({token}) returns {is_bool_str}')
#     return is_bool_str

# def is_list(token: str) -> bool:
#     """Return true if string represents a list"""
#     if token.startswith("[") and token.endswith("]"):
#         return True
#     return False

# def is_dict(token: str) -> bool:
#     """Return true if string represents a dictionary"""
#     if token.startswith("{") and token.endswith("}"):
#         return True
#     return False

# def make_list_from_string(token: str) -> list:
#     """Translate list formatted string to a list obj"""
#     text = token[1:-1]
#     return text.split(",")

# def make_dict_from_string(token: str) -> dict:
#     """Translate dict formatted string to a dict obj"""
#     text = token[1:-1]
#     entry_list = text.split(",")
#     result_dict = {}
#     LOGGER.debug(f'make_dict_from_string({token})')
#     for entry in entry_list:
#         key_val = entry.split(":")
#         LOGGER.debug(f'  key_val: {entry}')
#         key = key_val[0].strip()
#         value = key_val[1].strip()
#         if is_integer(value):
#             value=int(value)
#         elif is_boolean(value):
#             value = value in ['True', 'true']
#         result_dict[key] = value

#     LOGGER.debug(f'make_dict_from_string() returns: {result_dict}')
#     return result_dict

def build_kwargs_from_args(args: list) -> dict:
    kwargs = {}
    LOGGER.debug(f"build_kwargs_from_args('{args}')")
    for parm_block in args:
        # param_key=param_value OR param_key=[a,list,of,stuff]
        tokens = parm_block.split("=", 1)
        LOGGER.debug(f' parm_block: {parm_block}')
        LOGGER.debug(f'      tokens: {tokens}')
        if len(tokens) == 1:
            kwargs[tokens[0]] = ""
        else:
            if util.is_list(tokens[1]):
                kwargs[tokens[0]] = util.make_list_from_string(tokens[1])
            elif util.is_dict((tokens[1])):
                kwargs[tokens[0]] = util.make_dict_from_string(tokens[1])
            elif util.is_integer(tokens[1]):
                kwargs[tokens[0]] = int(tokens[1])
            elif util.is_boolean(tokens[1]):
                kwargs[tokens[0]] = tokens[1] in ['True', 'true']
            else:
                kwargs[tokens[0]] = tokens[1]
    
    LOGGER.debug(f'build_kwargs_from_args() returns: {kwargs}')
    return kwargs

def parse_input(args: list) -> Tuple[str, str, str, dict]:
    """Parse program CLI command parameters, return Namespace, Method, Parms as a tuple"""
    # cmd = None
    # sub_cmd = None
    parm_kwargs = {}
    namespace = None
    method = None
    reference = None
    if len(args) > 0:
        namespace = args[0]
        if args[0].count('.') > 1:
            reference = args[0]
            LOGGER.info(f'Looks like a reference: {reference}')
            # method = 'help'
        elif "." in namespace:
            # namespace.method
            tokens = namespace.split(".")
            namespace = tokens[0]
            method = tokens[1]
        if len(args) > 1:
            parm_kwargs = build_kwargs_from_args(args[1:])
    
    LOGGER.debug('Parsed Command Input:')
    LOGGER.debug(f'  Namespace : {namespace}')
    LOGGER.debug(f'  Method    : {method}')
    LOGGER.debug(f'  Reference : {reference}')
    LOGGER.debug(f'  kwargs    : {parm_kwargs}')

    return reference, namespace, method, parm_kwargs

# === Intro help page ================================================================================
def display_script_help(usage: str):
    """Display script help dialog to explain how program works"""
    print()
    print(f'kodi_cli: v{__version__}\n')
    print(usage)
    print('Commands are based on Kodi namespaces and methods for each namespace.  When executing a command')
    print('you supply the namespace, the method and any parameters (if required).\n')
    print('For example, to display the mute and volume level settings on host kodi001, type:\n')
    print('  kodi_cli -H kodi001 Application.GetProperties properties=[muted,volume]\n')
    print('TIPS - When calling the script')
    print(' - add -h to display script syntax and list of option parameters')
    print(' - enter HELP as the command for a list of available commands (namespaces)')
    print(' - add -C to create a config file with parameter defaults.\n')
    print('To create a configfile')
    print('  - Compose the command line with all the values desired as defaults')
    print('  - Append a -C to the end of the commandline, the file will be created (if it does not already exist)')
    print('  - Any future runs will use the defaults, which can be overridden if needed.\n')
    print('Help commands')
    print('  - list of namespaces:    kodi_cli Help')
    print('  - Methods for Namespace: kodi_cli Help Application')
    print('  - Parameters for Method: kodi_cli Help Application.GetProperties\n')
    print('Details for namespaces, methods and parameters may be found at https://kodi.wiki/view/JSON-RPC_API/v12')


# === Misc. routines =================================================================================
def setup_logging(settings_dict: dict):
    # TODO: Externalize logging settings
    import logging
    lg_format=settings_dict['log_format']
    lg_level = settings_dict['log_level']
    # logging.TRACE = logging.DEBUG + 5
    logging.basicConfig(format=lg_format, level=lg_level,)

def dump_args(args):
    LOGGER.debug('Runtime Settings:')
    LOGGER.debug('  Key             Value')
    LOGGER.debug('  --------------- -----------------------------------------------')
    if isinstance(args, dict):
        for k,v in args.items():
            if k == 'password':
                v = '*'*len(v)
            LOGGER.debug(f'  {k:15} {v}')
    else:    
        for entry in args._get_kwargs():
            LOGGER.debug(f'  {entry[0]:15} {entry[1]}')
    LOGGER.debug('  ---------------------------------------------------------------')


def display_program_info():
    kodi = KodiObj()
    # LOGGER.setLevel(logging.DEBUG)
    this_path = pathlib.Path(__file__).absolute().parent

    LOGGER.success('Calling Info-')
    LOGGER.info(f'  Command Line : {" ".join(sys.argv)}')
    LOGGER.info(f'  Current dir  : {os.getcwd()}')
    LOGGER.info(f'  Current root : {this_path}')
    LOGGER.success('Program Info-')
    LOGGER.info(f'  Version      : {cfg.__version__}')
    LOGGER.info(f'  Installed at : {this_path}')
    exists = 'exists' if cfg.CONFIG_EXISTS else 'does not exist'
    LOGGER.info(f'  Config       : {cfg.FILE_CONFIG}  [{exists}]')
    LOGGER.success('Host Info-')
    host_info = cfg.get_host_info()
    for k,v in host_info.items():
        LOGGER.info(f'  {k:13}: {v}')
    LOGGER.info(f'  API version  : {kodi._kodi_api_version}')
    LOGGER.info('')

def initialize_loggers(args: argparse.Namespace):
    log_filename = pathlib.Path(cfg.logging_filename) # pathlib.Path('./logs/da-photo.log')

    log_level = cfg.logging_level
    # if args.verbose:
    #     if args.verbose == 1:
    #         log_level = 'INFO'
    #     elif args.verbose == 2:
    #         log_level = 'DEBUG'
    #     elif args.verbose > 2:
    #         log_level = 'TRACE' 
        
    if log_level.upper() == 'INFO':
        console_format = cfg.DEFAULT_CONSOLE_LOGFMT
    else:
        console_format = cfg.DEBUG_CONSOLE_LOGFMT

    c_handle = cfg.configure_logger(log_format=console_format, log_level=log_level)
    f_handle = -1
    if cfg.logging_enabled:
        f_handle = cfg.configure_logger(log_filename, log_format=cfg.DEFAULT_FILE_LOGFMT, log_level=log_level,
                                       rotation=cfg.logging_rotation, retention=cfg.logging_retention)
        
    # Hack for future ability to dynamically change logging levels
    LOGGER.c_handle = c_handle
    LOGGER.f_handle = f_handle

    if len(cfg.logger_blacklist.strip()) > 0: 
        for logger_name in cfg.logger_blacklist.split(','):
            LOGGER.disable(logger_name)

def apply_overrides(args: argparse.Namespace):
    for key, val in args._get_kwargs():
        cfg_val = getattr(cfg, key, None)
        if cfg_val is not None and cfg_val != val:
            LOGGER.debug(f'CmdLine Override: {key}: {val}')
            setattr(cfg, key, val)
    
    if args.verbose:
        if args.verbose == 1:
            cfg.logging_level = 'INFO'
        elif args.verbose == 2:
            cfg.logging_level = 'DEBUG'
        elif args.verbose > 2:
            cfg.logging_level = 'TRACE'

# ==== Main script body =================================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description=f'Kodi CLI controller  v{__version__}')
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = textwrap.dedent('''\
        command is formatted as follows:
            Namespace.Method [parameter [parameter] [...]]

        example - Retrieve list of 5 addons:
            kodi-cli -H myHost Addons.GetAddons properties=[name,version,summary] limits={start:0,end:5}
        ''')
    parser.add_argument("-H","--host", type=str, default=cfg.host, help="Kodi hostname")
    parser.add_argument("-P","--port", type=int, default=cfg.port,help="Kodi RPC listen port")
    parser.add_argument("-u","--kodi-user", type=str, default=cfg.kodi_user,help="Kodi authenticaetion username")
    parser.add_argument("-p","--kodi_pw", type=str, default=cfg.kodi_pw,help="Kodi autentication password")
    parser.add_argument('-C','--create_config', action='store_true', help='Create default config')
    parser.add_argument('-CO','--create_config_overwrite', action='store_true', help='Create default config, overwrite if exists')
    parser.add_argument("-f","--format_output", action="store_true", default=cfg.format_output,help="Format json output")
    parser.add_argument('-c',"--csv-output", action="store_true", default=cfg.csv_output,help="Format csv output (only specific commands)")    
    parser.add_argument("-v","--verbose", action='count', help="Verbose output, -v = INFO, -vv = DEBUG, -vvv TRACE")
    parser.add_argument("-i","--info", action='store_true', help='display program info and quit')
    parser.add_argument("command", type=str, nargs='*', help="RPC command  namespace.method (help namespace to list)")
    args = parser.parse_args()
    
    apply_overrides(args)
    initialize_loggers(args)

    if args.create_config or args.create_config_overwrite:
        # create_config(args)
        try:
            if args.create_config_overwrite:
                cfg.create_template_config(overwrite=True)
            else:
                cfg.create_template_config(overwrite=False)
            return 0
        except Exception as ex:
            LOGGER.critical(repr(ex))
            return -1
        
    if args.info:
        display_program_info()
        # dump_args(args_dict)
        return 0

    if not args.command:
        display_script_help(parser.format_usage())
        return -1  # missing arguments

    kodi = KodiObj(cfg.host, cfg.port, cfg.kodi_user, cfg.kodi_pw, cfg._json_rpc_loc)

    # Process command-line input
    reference, namespace, method, param_dict = parse_input(args.command)
    if reference:
        kodi.help(reference)
        return 0

    if namespace == "help":
        kodi.help()
        return 0

    method_sig = f'{namespace}.{method}'
    if 'help' in param_dict.keys():
        kodi.help(method_sig)
        return 0

    if not kodi.check_command(namespace, method):
        kodi.help(method_sig)
        return -2
    
    factory = output_factory.ObjectFactory()
    factory.register_builder("CSV", output_factory.CSV_OutputServiceBuilder())
    factory.register_builder("JSON", output_factory.JSON_OutputServiceBuilder())

    kodi.send_request(namespace, method, param_dict)
    response = kodi.response_text
    if cfg.csv_output and method_sig in kodi.CSV_CAPABLE_COMMANDS.keys():
        json_node = kodi.CSV_CAPABLE_COMMANDS[method_sig]
        output_obj = factory.create("CSV", response_text=response, list_key=json_node)
    else:
        if cfg.csv_output:
            LOGGER.info('csv option is not available for this command...')
        if cfg.format_output:
            pretty = True
        else:
            pretty = False
        output_obj = factory.create("JSON", response_text=response, pretty=pretty)
    
    output_obj.output_result()    
    return kodi.response_status_code

if __name__ == "__main__":
    sys.exit(main())
