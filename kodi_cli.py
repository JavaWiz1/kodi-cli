import argparse
import csv
import json
import logging
import os
import pathlib
import sys
import textwrap

import kodi_output_factory as output_factory
import version as ver_info
from kodi_interface import KodiObj

__version__ = importlib.metadata.version("kodi-cli")

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
    

LOGGER = logging.getLogger(__name__)
DFLT_LOG_FORMAT = "[%(levelname)-5s] %(message)s"
DFLT_LOG_LEVEL = logging.ERROR

__version__ = ver_info.get_version("kodi-cli")

# === Validation routines =================================================
def is_integer(token: str) -> bool:
    """Return true if string is an integer"""
    is_int = True
    try:
        int(token)
    except ValueError:
        is_int = False
    return is_int

def is_boolean(token: str) -> bool:
    """Return true if string is a boolean"""
    is_bool_str = False
    if token in ["True", "true", "False", "false"]:
        is_bool_str = True
    LOGGER.debug(f'  is_boolean({token}) returns {is_bool_str}')
    return is_bool_str

def is_list(token: str) -> bool:
    """Return true if string represents a list"""
    if token.startswith("[") and token.endswith("]"):
        return True
    return False

def is_dict(token: str) -> bool:
    """Return true if string represents a dictionary"""
    if token.startswith("{") and token.endswith("}"):
        return True
    return False

def make_list_from_string(token: str) -> list:
    """Translate list formatted string to a list obj"""
    text = token[1:-1]
    return text.split(",")

def make_dict_from_string(token: str) -> dict:
    """Translate dict formatted string to a dict obj"""
    text = token[1:-1]
    entry_list = text.split(",")
    result_dict = {}
    LOGGER.debug(f'make_dict_from_string({token})')
    for entry in entry_list:
        key_val = entry.split(":")
        LOGGER.debug(f'  key_val: {entry}')
        key = key_val[0].strip()
        value = key_val[1].strip()
        if is_integer(value):
            value=int(value)
        elif is_boolean(value):
            value = value in ['True', 'true']
        result_dict[key] = value

    LOGGER.debug(f'make_dict_from_string() returns: {result_dict}')
    return result_dict

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
            if is_list(tokens[1]):
                kwargs[tokens[0]] = make_list_from_string(tokens[1])
            elif is_dict((tokens[1])):
                kwargs[tokens[0]] = make_dict_from_string(tokens[1])
            elif is_integer(tokens[1]):
                kwargs[tokens[0]] = int(tokens[1])
            elif is_boolean(tokens[1]):
                kwargs[tokens[0]] = tokens[1] in ['True', 'true']
            else:
                kwargs[tokens[0]] = tokens[1]
    
    LOGGER.debug(f'build_kwargs_from_args() returns: {kwargs}')
    return kwargs

def parse_input(args: list) -> (str, str, str, dict):
    """Parse program CLI command parameters, return Namespace, Method, Parms as a tuple"""
    cmd = None
    sub_cmd = None
    parm_kwargs = {}
    namespace = None
    method = None
    reference = None
    if len(args) > 0:
        namespace = args[0]
        if args[0].count('.') > 1:
            reference = args[0]
            print(f'Looks like a reference: {reference}')
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


# === Config file routines ========================================================================
def create_config(args) -> bool:
    """Create config dictionary based on config file and command-line parameters"""
    this_path = pathlib.Path(__file__).absolute().parent
    cfg_file = this_path / "kodi_cli.cfg"
    if cfg_file.exists():
        print('ERROR- request to create config file, but it already exists.  Rename or delete.')
        print(f'       {cfg_file}')
        return False

    cfg_dict = get_configfile_defaults(args)
    # Remove keys we don't want in the config
    for key in ['config', 'create_config', 'command', '__version__']:
        try:
            cfg_dict.pop(key)
        except KeyError:
            pass
    # Remove keys that don't have a value
    cfg_dict = {key:val for key, val in cfg_dict.items() if val is not None}
    # Convert to json format and save
    cfg_json = json.dumps(cfg_dict, indent=2)
    with open(cfg_file,"w")as cfg_fh:
        cfg_fh.write(cfg_json)

    print(f'{cfg_file} created.')
    return True

def get_configfile_defaults(cmdline_args: dict = None) -> dict:
    """Get configfile defaults.  Optionally, apply command-line over-rides"""
    # if cfg file exists, us it, otherwise hard-coded defaults
    default_cfg_dict = {
                "host": "localhost", 
                "port": 8080,
                "user": "kodiuser",
                "password": "kodipassword",
                "format_output": False,
                "csv_output": False,
                "json_rpc_loc": "./json-defs",
                "log_format": f"{DFLT_LOG_FORMAT}",
                "log_level": DFLT_LOG_LEVEL
    }

    this_path = pathlib.Path(__file__).absolute().parent
    cfg_file = this_path / "kodi_cli.cfg"
    final_dict = {}
    try:
        # Use the config file
        with open(cfg_file, "r") as cfg_fh:
            cfg_dict = json.load(cfg_fh)   
    except FileNotFoundError:
        cfg_dict = {}

    final_dict = {**default_cfg_dict, **cfg_dict}    
    #  Over-ride with command-line parms
    if cmdline_args:
        for entry in cmdline_args._get_kwargs():
            if entry[1]:
                final_dict[entry[0]] = entry[1]
    # add version
    final_dict["__version__"] = __version__

    return final_dict

# === Intro help page ================================================================================
def display_script_help(usage: str):
    """Display script help dialog to explain how program works"""
    print()
    print(__version__)
    print(usage)
    print('Commands are based on Kodi namespaces and methods for each namespace.  When executing a command')
    print('you supply the namespace, the method and any parameters (if required).\n')
    print('For example, to display the mute and volume level settings on host kodi001, type:\n')
    print('  python kodi_cli.py -H kodi001 Application.GetProperties properties=[muted,volume]\n')
    print('TIPS - When calling the script')
    print(' - add -h to display script syntax and list of option parameters')
    print(' - enter HELP as the command for a list of available commands (namespaces)')
    print(' - add -C to create a config file with parameter defaults.\n')
    print('To create a configfile')
    print('  - Compose the command line with all the values desired as defaults')
    print('  - Append a -C to the end of the commandline, the file will be created (if it does not already exist)')
    print('  - Any future runs will use the defaults, which can be overridden if needed.\n')
    print('Help commands')
    print('  - list of namespaces:    python kodi_cli.py Help')
    print('  - Methods for Namespace: python kodi_cli.py Help Application')
    print('  - Parameters for Method: python kodi_cli.py Help Application.GetProperties\n')
    print('Details for namespaces, methods and parameters may be found at https://kodi.wiki/view/JSON-RPC_API/v12')


# === Misc. routines =================================================================================
def setup_logging(settings_dict: dict):
    # TODO: Externalize logging settings 
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
    LOGGER.setLevel(logging.DEBUG)
    this_path = pathlib.Path(__file__).absolute().parent

    LOGGER.debug('Calling Info-')
    LOGGER.debug(f'  Command Line : {" ".join(sys.argv)}')
    LOGGER.debug(f'  Current dir  : {os.getcwd()}')
    LOGGER.debug(f'  Current root : {this_path}')
    LOGGER.debug('')
    LOGGER.debug('Host Info-')
    host_info = ver_info.get_host_info()
    for k,v in host_info.items():
        LOGGER.debug(f'  {k:13}: {v}')
    LOGGER.debug(f'  API version  : {kodi._kodi_api_version}')
    LOGGER.debug('')

# ==== Main script body =================================================================================
def main() -> int:
    default = get_configfile_defaults()
    parser = argparse.ArgumentParser(description=f'Kodi CLI controller  v{__version__}')
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = textwrap.dedent('''\
        command is formatted as follows:
            Namespace.Method [parameter [parameter] [...]]

        example - Retrieve list of 5 addons:
            kodi-cli -H myHost Addons.GetAddons properties=[name,version,summary] limits={start:0,end:5}
        ''')
    parser.add_argument("-H","--host", type=str, default=default['host'], help="Kodi hostname")
    parser.add_argument("-P","--port", type=int, default=default['port'],help="Kodi RPC listen port")
    parser.add_argument("-u","--user", type=str, default=default['user'],help="Kodi authenticaetion username")
    parser.add_argument("-p","--password", type=str, default=default['password'],help="Kodi autentication password")
    parser.add_argument('-C','--create_config', action='store_true', help='Create empty config')
    parser.add_argument("-f","--format_output", action="store_true", default=default['format_output'],help="Format json output")
    parser.add_argument('-c',"--csv", action="store_true", default=default['csv_output'],help="Format csv output (only specific commands")    
    parser.add_argument("-v","--verbose", action='count', help="Verbose output, -v = INFO, -vv = TRACE, -vvv DEBUG")
    parser.add_argument("-i","--info", action='store_true', help='display program info and quit')
    parser.add_argument("command", type=str, nargs='*', help="RPC command  namespace.method (help namespace to list)")
    args = parser.parse_args()
    
    # print(f'** args: {args.command}')

    if args.create_config:
        create_config(args)
        return 0

    # Create args/settings dict from cmdline and config file
    args_dict = get_configfile_defaults(args)
    
    loglvl = default['log_level']
    logging.TRACE = logging.DEBUG + 5
    if args.verbose:
        # Command line over-ride
        if args.verbose == 1:
            loglvl = logging.INFO
        elif args.verbose == 2:
            loglvl=logging.TRACE
        elif args.verbose > 2:
            loglvl = logging.DEBUG

    if loglvl != args_dict['log_level']:
        # print(f'log level over-ride, from: {args_dict["log_level"]} to {loglvl}')
        args_dict['log_level'] = loglvl

    setup_logging(args_dict)
    if args.info:
        display_program_info()
        dump_args(args_dict)
        return 0

    if not args.command:
        display_script_help(parser.format_usage())
        return -1  # missing arguments

    kodi = KodiObj(args_dict['host'], args_dict['port'], args_dict['user'], args_dict['password'], args_dict['json_rpc_loc'])
    if loglvl < logging.ERROR:
        dump_args(args_dict)

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
    if args.csv and method_sig in kodi.CSV_CAPABLE_COMMANDS.keys():
        json_node = kodi.CSV_CAPABLE_COMMANDS[method_sig]
        output_obj = factory.create("CSV", response_text=response, list_key=json_node)
    else:
        if args.csv:
            LOGGER.info('csv option is not available for this command...')
        if args.format_output:
            pretty = True
        else:
            pretty = False
        output_obj = factory.create("JSON", response_text=response, pretty=pretty)
    
    output_obj.output_result()    
    return kodi.response_status_code

if __name__ == "__main__":
    sys.exit(main())
