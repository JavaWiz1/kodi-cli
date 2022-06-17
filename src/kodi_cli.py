import argparse
import json
import logging
import os
import inspect
import requests
import pathlib

LOGGER = logging.getLogger(__name__)

class KodiObj():
    def __init__(self, host: str, port: int, user: str, password: str):
        self._LOGGER = logging.getLogger(__name__)
        self._LOGGER.debug("KodiObj created")
        self._host = host
        self._port = port
        self._userid = user
        self._password = password
        json_dict = self._load_kodi_namespaces()
        self._namespaces = json_dict['namespaces']
        self._kodi_references = json_dict['references']
        self._base_url = f'http://{host}:{port}/jsonrpc'
        self._error_json = {
                                "error": {
                                    "code": -1,
                                    "data": {
                                    "method": "TBD"
                                    },
                                    "message": "Invalid params."
                                }
                            }
    def get_namespace_list(self) -> list:
        """Returns a list of the Kodi namespace objeccts"""
        return self._namespaces.keys()
    
    def get_namespace_method_list(self, namespace: str) -> list:
        """Returns a list of the methods for the requested namespace"""
        commands = []
        ns = self._namespaces.get(namespace, None)
        if ns:
            commands = ns.keys()
        return commands
    
    def check_command(self, namespace: str, method: str) -> bool:
        """Validate namespace method combination, true if valid, false if not"""
        self._LOGGER.debug(f'Check Command: {namespace}.{method}')
        if namespace not in self._namespaces.keys():
            self._LOGGER.error(f'Invalid namespace \'{namespace}')
            return False
        if method:
            if method not in self._namespaces[namespace].keys():
                self._LOGGER.error(f'\'{method}\' is not valid method\' for namespace \'{namespace}\'')
                return False
        else:
            self._LOGGER.error(f'Must supply Method for namespace \'{namespace}\'')
            return False

        param_template = json.loads(self._namespaces[namespace][method])
        if param_template['description'] == "NOT IMPLEMENTED.":
            self._LOGGER.error(f'{namespace}.{method} has not been implemented')
            return False
        # TODO: Check for required parameters
        self._LOGGER.debug(f'  {namespace}.{method} is valid.')
        return True

    def send_request(self, namespace: str, command: str, input_params: dict) -> bool:
        """Send Namesmpace.Method command to target host"""
        method = f'{namespace}.{command}'
        self._LOGGER.debug(f'Load Command Template : {method}')
        param_template = json.loads(self._namespaces[namespace][command])
        parm_list = param_template['params']
        self._LOGGER.debug(f'  template:  {param_template}')
        self._LOGGER.debug(f'  parm_list: {parm_list}')
        req_parms = {}
        self._LOGGER.debug('  Parameter dictionary:')
        for parm_entry in parm_list:
            parm_name = parm_entry['name']
            parm_value = input_params.get(parm_name,None)
            if not parm_value:
                parm_value = parm_entry.get('default', None)
            self._LOGGER.debug(f'    Key    : {parm_name:15}  Value: {parm_value}')
            req_parms[parm_name] = parm_value
        self._LOGGER.debug('')
        return self._call_kodi(method, req_parms)

    def help(self, input_string: str = None):
        namesp = None
        method = None
        if input_string:
            if "." in input_string:
                tokens = input_string.split(".")
                namesp = tokens[0]
                method = tokens[1]
            else:
                namesp = input_string

        self._LOGGER.debug(f'Help - {input_string}')
        self._LOGGER.debug(f'  Namesapce : {namesp}')
        self._LOGGER.debug(f'  Method    : {method}')

        if not namesp or (namesp == "help"):
            self._help_namespaces()
            return

        if namesp not in self._namespaces.keys():
            print(f'Unknown namespace \'{namesp}\'. Try help namespaces')
            return

        if not method or method == "None":
            self._help_namespace(namesp)
            return
        
        if method not in self.get_namespace_method_list(namesp):
            self._help_namespace(namesp)
            # print(f'Unknown command [{method}] in namespace {namesp}')
            return

        self._help_namespace_method(namesp, method)

    # === Private Class Fuctions ==============================================================
    def _load_kodi_namespaces(self) -> dict:
        """Load kodi namespace definition from configuration json file"""
        this_path = os.path.dirname(os.path.abspath(__file__))
        json_file = f'{this_path}{os.sep}kodi_namespaces.json'
        with open(json_file,"r") as json_fh:
            json_data = json.load(json_fh)
        return json_data

    def _clear_response(self):
        self.response_text = None
        self.response_status_code = None
        self.request_success = False

    def _set_response(self, code: int, text: str, success: bool = False):
        self.response_status_code = code
        self.response_text = text
        self.request_success = success

    def _client_call(self) -> bool:
        ret_value = False

        return ret_value

    def _call_kodi(self, method: str, params: dict = {}) -> bool:
        self._clear_response()
        MAX_RETRY = 2
        payload = {"jsonrpc": "2.0", "id": 1, "method": f"{method}", "params": params }
        headers = {"Content-type": "application/json"}
        self._LOGGER.debug(f'Prep call to {self._host}')
        self._LOGGER.debug(f"  URL    : {self._base_url}")
        self._LOGGER.debug(f"  Method : {method}")
        self._LOGGER.debug(f"  Payload: {payload}")

        retry = 0
        success = False  # default for 1st loop cycle
        while not success and retry < MAX_RETRY:
            try:
                self._LOGGER.debug(f'  Making call to {self._base_url} for {method}')
                # TODO: change to http.client to avoid requests package dependency
                # https://docs.python.org/3/library/http.client.html
                resp = requests.post(self._base_url,
                                    auth=(self._userid, self._password),
                                    data=json.dumps(payload),
                                    headers=headers, timeout=(5,3)) # connect, read
                success = True
                #self._LOGGER.debug(f"{self._host}: {resp.status_code} - {resp.text}")
            except requests.RequestException as re:
                retry = MAX_RETRY + 1
                self._error_json['error']['code'] = -2
                self._error_json['error']['data']['method'] = method
                # self._error_json['error']['message'] = re.__class__.__name__
                self._error_json['error']['message'] = repr(re)
                self._set_response(-2, json.dumps(self._error_json))
                # self._set_response(-2, f'{{"result": "{re.__class__.__name__}"}}')
            except Exception as ce:
                retry += 1
                if not hasattr(ce, "message"):
                    self._error_json['error']['code'] = -3
                    self._error_json['error']['code']['data']['method'] = method
                    self._error_json['error']['message'] = repr(ce)
                    self._set_response(-2, json.dumps(self._error_json))
                    # self._set_response(-2, json.dumps({"result": repr(ce)}))
                    self._LOGGER.error(f'Exception{retry}: {resp}')
                time.sleep(2)

        if success:
            self._set_response(resp.status_code, resp.text, True)

        # print(f"  [{self.request_success}] ({self.response_status_code}) {self.response_text}")
        return success

    def _help_namespaces(self):
        print("\nKodi namespaces -")
        print("   Namespace       Methods")
        print("   --------------- ---------------------------------------------------------------------------")
        for ns in self.get_namespace_list():
            methods = ""
            for method in self.get_namespace_method_list(ns):
                if len(methods) == 0:
                    methods = method
                elif len(methods) + len(method) > 70:
                    print(f'   {ns:15} {methods},')
                    ns = ""
                    methods = method
                else:
                    methods = f"{methods}, {method}"
            print(f'   {ns:15} {methods}\n')

    def _help_namespace(self, ns: str):
        ns_commands = self.get_namespace_method_list(ns)

        print(f'\n{ns} Namespace Methods -')
        print('  Method                    Description')
        print('  ------------------------- --------------------------------------------')
        for token in ns_commands:
            def_block = json.loads(self._namespaces[ns][token])
            description = def_block['description']
            method = f'{ns}.{token}'
            print(f'  {method:25} {description}')

    def _help_namespace_method(self, ns: str, method: str):
        help_json = json.loads(self._namespaces[ns][method])
        print()
        p_names = self._get_parameter_names(help_json.get('params',[]))
        print('-------------------------------------------------------------------------------')
        print(f'Signature   : {ns}.{method}({p_names})')
        print(f'Description : {help_json["description"]}')

        if len(help_json.get('params',[])) > 0:
            print('-------------------------------------------------------------------------------')
            for param in help_json['params']:
                p_name = self._get_parameter_value(param,'name',"Unknown")
                p_desc = self._get_parameter_value(param, 'description')
                p_ref = self._get_parameter_value(param, '$ref')
                p_types = self._get_types(param)
                p_req = self._get_parameter_value(param,'required', "False")
                p_values = self._get_reference_values(param)
                p_default = self._get_parameter_value(param,'default')
                p_min_items = self._get_parameter_value(param, 'minItems')
                p_min = self._get_parameter_value(param,'minimum')
                p_max = self._get_parameter_value(param,'maximum')
                print(f'{p_name}')
                self._print_parameter_line('Desc', p_desc)
                self._print_parameter_line('Type', p_types)
                self._print_parameter_line('Min Items', p_min_items)
                self._print_parameter_line('Required', p_req)
                self._print_parameter_line('Reference', p_ref)
                self._print_parameter_line('Values', p_values)
                self._print_parameter_line('Minimum', p_min)
                self._print_parameter_line('Maximum', p_max)
                self._print_parameter_line('Default', p_default)

        self._LOGGER.info(f'{json.dumps(help_json,indent=2)}')

    def _print_parameter_line(self, caption: str, value: str):
        if value:
            print(f'   {caption:9}: {value}')

    def _get_parameter_value(self, p_dict: dict, key: str, default: str = None) -> str:
        token = p_dict.get(key, default)
        if token:
            token = str(token)
        return token

    def _get_parameter_names(self, json_param_list: list) -> list:
        name_list = []
        for p_entry in json_param_list:
            if p_entry.get('required', False) == True:
                name_list.extend([p_entry['name']])
            else:
                name_list.extend([f"[{p_entry['name']}]"])
        return ', '.join(name_list)

    def _get_types(self, param: dict) -> str:
        param_type = param.get('type', "String")
        return_types = type(param_type)
        self._LOGGER.debug(f'_get_types for: {param}')
        if type(param_type) is str:
            return_types = param_type
        elif type(param_type) is list:
            types_list = []
            return_types = ""
            for token_type in param_type:
                if "type" in token_type:
                    types_list.extend([token_type['type']])
                elif "$ref" in token_type:
                    ref_types = self._get_reference_types(token_type)
                    types_list.extend(ref_types.split('|'))

            return_types += '|'.join(list(set(types_list)))
            
        self._LOGGER.debug(f'_get_types returns: {return_types}')
        return return_types

    def _get_reference_types(self, param: dict) -> str:
        types = None
        ref_dict = self._get_reference_id_definition(param)
        if ref_dict:
            r_types = ref_dict['type']
            ret_types = []
            if type(r_types) is str:
                ret_types.extend([r_types])
            elif type(r_types) is list:
                for r_type in ref_dict['type']:
                    ret_types.extend(r_type['type'])
            types = '|'.join(ret_types)
        
        return types

    def _get_reference_values(self, param: dict) -> str:
        values = None
        ref_dict = self._get_reference_id_definition(param)
        if not ref_dict:
            ref_dict = param
        if ref_dict:
            r_types = ref_dict.get('type')
            r_enums = []
            if type(r_types) is str:
                r_enums = ref_dict.get('enums',[])
            elif type(r_types) is list:
                for r_type in ref_dict['type']:
                    if r_type.get('enums'):
                        r_enums.extend(r_type['enums'])
                    elif r_type.get('type') == 'boolean':
                        r_enums.extend([ 'True', 'False' ])
                    elif r_type.get('type') == 'integer':
                        r_max = r_type.get('maximum')
                        r_min = r_type.get('minimum')
                        if r_max:
                            r_enums.extend([f'{r_min}..{r_max}'])

            values = ','.join(r_enums)

        return values

    def _get_reference_id_definition(self, param: dict) -> str:
        id = param.get('$ref')
        ref_dict = self._kodi_references.get(id)
        if ref_dict:
            self._LOGGER.debug(f'Retrieved referenceId: {id}')
        else:
            self._LOGGER.debug(f'No reference found for: {id}')
        return ref_dict 

# =======================================================================================================================
# === Module Functions ==================================================================================================
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
                        "format_output": False 
                   }
    #  Over-ride with command-line parms
    if cmdline_args:
        for entry in cmdline_args._get_kwargs():
            if entry[1]:
                cfg_dict[entry[0]] = entry[1]

    return cfg_dict

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

def setup_logging(log_level):
    lg_format='[%(levelname)-5s] %(message)s'
    logging.basicConfig(format=lg_format, level=log_level,)

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

def main():
    default = get_configfile_defaults(None)
    parser = argparse.ArgumentParser()
    parser.add_argument("-H","--host", type=str, default=default['host'], help="Kodi hostname")
    parser.add_argument("-P","--port", type=int, default=default['port'],help="Kodi RPC listen port")
    parser.add_argument("-u","--user", type=str, default=default['user'],help="Kodi authenticaetion username")
    parser.add_argument("-p","--password", type=str, default=default['password'],help="Kodi autentication password")
    parser.add_argument('-c',"--config", type=str, help="Optional config file")
    parser.add_argument('-C','--create_config', action='store_true', help='Create empty config')
    parser.add_argument("-f","--format_output", action="store_true", default=default['format_output'],help="Format json output")
    parser.add_argument("-v","--verbose", action='count', help="Turn out verbose output, more parms increase verbosity")
    parser.add_argument("command", type=str, nargs='*', help="RPC command  namespace.method (help namespace to list)")
    args = parser.parse_args()
  
    if args.create_config:
        create_config(args)
        return

    if not args.command:
        display_script_help(parser.format_usage())
        return  

    # Create args/settings dict from cmdline and config file
    args_dict = get_configfile_defaults(args)
    
    loglvl = logging.ERROR
    if args.verbose:
        if args.verbose == 1:
            loglvl = logging.INFO
        elif args.verbose > 1:
            loglvl=logging.DEBUG
    
    setup_logging(loglvl)

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

    else:
        kodi.send_request(namespace, method, param_dict)
        response = kodi.response_text
        if args.format_output:
            response = json.dumps(json.loads(kodi.response_text), indent=2)
        print(response)


if __name__ == "__main__":
    main()
