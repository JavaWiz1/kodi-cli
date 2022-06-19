import argparse
import json
import logging
import os
import pathlib
import sys

from kodi_interface import KodiObj

LOGGER = logging.getLogger(__name__)
DFLT_LOG_FORMAT = "[%(levelname)-5s] %(message)s"
DFLT_LOG_LEVEL = logging.ERROR


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
    is_bool = False
    if token in ["True", "true", "False", "false"]:
        is_bool = True
    return is_bool

def is_list(token: str) -> bool:
    """Return true if string represents a list"""
    is_list = False
    if token.startswith("[") and token.endswith("]"):
        is_list = True
    return is_list

def make_list_from_string(token: str) -> list:
    """Translate list formatted string to a list"""
    text = token[1:-1]
    return text.split(",")


def parse_input(args: list) -> (str, str, dict):
    """Parse program CLI command parameters, return Namespace, Method, Parms as a tuple"""
    cmd = None
    sub_cmd = None
    parm_kwargs = {}
    namespace = None
    method = None
    if len(args) > 0:
        namespace = args[0]
        if "." in namespace:
            # namespace.method
            tokens = namespace.split(".")
            namespace = tokens[0]
            method = tokens[1]
        if len(args) > 1:
            for parm_block in args[1:]:
                # param_key=param_value
                # param_key=[a,list,of,stuff]
                tokens = parm_block.split("=")
                if len(tokens) == 1:
                    parm_kwargs[tokens[0]] = ""
                else:
                    if is_list(tokens[1]):
                        parm_kwargs[tokens[0]] = make_list_from_string(tokens[1])
                    elif is_integer(tokens[1]):
                        parm_kwargs[tokens[0]] = int(tokens[1])
                    elif is_boolean(tokens[1]):
                        parm_kwargs[tokens[0]] = bool(tokens[1])
                    else:
                        parm_kwargs[tokens[0]] = tokens[1]

    LOGGER.debug('Parsed Command Input:')
    LOGGER.debug(f'  Namespace : {namespace}')
    LOGGER.debug(f'  Method    : {method}')
    LOGGER.debug(f'  kwargs    : {parm_kwargs}')
    return namespace, method, parm_kwargs


# === Config file routines ========================================================================
def create_config(args) -> bool:
    """Create config dictionary based on config file and command-line parameters"""
    this_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file = f'{this_path}{os.sep}kodi_cli.cfg'
    if pathlib.Path(cfg_file).exists():
        print('ERROR- request to create config file, but it already exists.  Rename or delete.')
        print(f'       {cfg_file}')
        return False

    cfg_dict = get_configfile_defaults(args)
    # Remove keys we don't want in the config
    for key in ['config', 'create_config', 'command']:
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

def get_configfile_defaults(cmdline_args) -> dict:
    """Get configfile defaults"""
    # if cfg file exists, us it, otherwise hard-coded defaults
    this_path = os.path.dirname(os.path.abspath(__file__))
    cfg_file = f'{this_path}{os.sep}kodi_cli.cfg'
    try:
        # Use the config file
        with open(cfg_file, "r") as cfg_fh:
            cfg_dict = json.load(cfg_fh)
        
    except FileNotFoundError:
        # Use hard-coded defaults
        cfg_dict = {
                        "host": "localhost", 
                        "port": 8080,
                        "user": "kodiuser",
                        "password": "kodipassword",
                        "format_output": False, 
                        "log_format": f"{DFLT_LOG_FORMAT}",
                        "log_level": DFLT_LOG_LEVEL
                   }
    #  Over-ride with command-line parms
    if cmdline_args:
        for entry in cmdline_args._get_kwargs():
            if entry[1]:
                cfg_dict[entry[0]] = entry[1]

    return cfg_dict

# === Intro help page ================================================================================
def display_script_help(usage: str):
    """Display script help dialog to explain how program works"""
    print()
    print(usage)
    print('Commands are based on Kodi namespaces and methods for each namespace.  When executing a command')
    print('you supply the namespace, the method and any parameters (if required).\n')
    print('For example, to display the mute and volume level settings on host kodi001, type:\n')
    print('  python kodi_cli.py -H kodi001 Application.GetProperties properties=[muted,volume]\n')
    print('TIPS - When calling the script:')
    print(' - add -h to display script syntax and list of option parameters')
    print(' - enter HELP as the command for a list of available commands (namespaces)')
    print(' - add -C to create a config file for paraneter defaults.\n')
    print('To create a configfile:')
    print('  - Compose the command line with all the values desired as defaults')
    print('  - Append a -C to the end of the commandline, the file will be created (if it does not already exist)')
    print('  - Any future runs will use the defaults, which can be overridden if needed.\n')
    print('Help commands:')
    print('  - list of namespaces:    python kodi_cli.py Help')
    print('  - Methods for Namespace: python kodi_cli.py Help Application')
    print('  - Parameters for Method: python kodi_cli.py Help Application.GetProperties\n')
    print('Details for namespaces, methods and parameters may be found at https://kodi.wiki/view/JSON-RPC_API/v12')


# === Misc. routines =================================================================================
def setup_logging(settings_dict: dict):
    # TODO: Externalize logging settings 
    lg_format=settings_dict['log_format']
    lg_level = settings_dict['log_level']
    logging.basicConfig(format=lg_format, level=lg_level,)

def dump_args(args):
    LOGGER.debug('Runtime Settings:')
    LOGGER.debug('  Key             Value')
    LOGGER.debug('  --------------- -----------------------------------------------')
    if isinstance(args, dict):
        for k,v in args.items():
            LOGGER.debug(f'  {k:15} {v}')
    else:    
        for entry in args._get_kwargs():
            LOGGER.debug(f'  {entry[0]:15} {entry[1]}')

def display_defaults(dflt_dict: dict):
    print('Defaults:')
    print('Key             Value')
    print(f"{'—'*15} {'—'*30}")
    for key, val in dflt_dict.items():
        print(f'{key:15} {val}')
    print()


# ==== Main script body =================================================================================
def main() -> int:
    default = get_configfile_defaults(None)
    parser = argparse.ArgumentParser()
    parser.add_argument("-H","--host", type=str, default=default['host'], help="Kodi hostname")
    parser.add_argument("-P","--port", type=int, default=default['port'],help="Kodi RPC listen port")
    parser.add_argument("-u","--user", type=str, default=default['user'],help="Kodi authenticaetion username")
    parser.add_argument("-p","--password", type=str, default=default['password'],help="Kodi autentication password")
    parser.add_argument('-C','--create_config', action='store_true', help='Create empty config')
    parser.add_argument('-l','--list', action='store_true', help='List defaults to console')
    parser.add_argument("-f","--format_output", action="store_true", default=default['format_output'],help="Format json output")
    parser.add_argument("-v","--verbose", action='count', help="Verbose output, -v = INFO, -vv = DEBUG")
    parser.add_argument("command", type=str, nargs='*', help="RPC command  namespace.method (help namespace to list)")
    args = parser.parse_args()
  
    if args.create_config:
        create_config(args)
        return 0

    if args.list:
        display_defaults(default)
        return 0

    if not args.command:
        display_script_help(parser.format_usage())
        return -1  # missing arguments

    # Create args/settings dict from cmdline and config file
    args_dict = get_configfile_defaults(args)
    
    loglvl = default['log_level'] # init from config setting
    if args.verbose:
        if args.verbose == 1:
            loglvl = logging.INFO
        elif args.verbose > 1:
            loglvl=logging.DEBUG
    if loglvl != args_dict['log_level']:
        print(f'log level over-ride, from: {args_dict["log_level"]} to {loglvl}')
        args_dict['log_level'] = loglvl

    setup_logging(args_dict)

    kodi = KodiObj(args_dict['host'], args_dict['port'], args_dict['user'], args_dict['password'])
    if loglvl < logging.ERROR:
        dump_args(args_dict)

    namespace, method, param_dict = parse_input(args.command)
    
    if namespace == "help":
        kodi.help()

    elif 'help' in param_dict.keys():
        kodi.help(f'{namespace}.{method}')

    elif not kodi.check_command(namespace, method):
        kodi.help(f'{namespace}.{method}')
        return -2
    else:
        kodi.send_request(namespace, method, param_dict)
        response = kodi.response_text
        if args.format_output:
            response = json.dumps(json.loads(kodi.response_text), indent=2)
        print(response)
        return kodi.response_status_code

    return 0

if __name__ == "__main__":
    sys.exit(main())
