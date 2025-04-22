import json
from loguru import logger as LOGGER
import os
import pathlib
import socket
import time
import requests
from typing import Tuple

# TODO:
#   Edit parameters prior to call for cleaner error messages
#   Parse parameter json better

class HelpParameter():
    _max_rows = 0
    _max_cols = 0
    
    def __init__(self, parameter_dict: dict = None, reference_dict: dict = None):
        self._parameter_block = parameter_dict
        self._reference_block = reference_dict

        self.name = None
        self.description = None
        self.default = ""
        self.minItems = None
        self.minLength = None
        self.minimum = None
        self.properties = None
        self.required = None
        self.types = None
        self.uniqueItems = None
        self.reference = None
        self.values = ""

        self._parameter_block = parameter_dict
        self._reference_block = reference_dict
        self._get_console_size()
        
    
    def populate(self):
        LOGGER.trace(f'populate() - block: {self._parameter_block}')
        self._populate_from_param_dict()
        if self.reference:
            self.values += self._populate_values_from_reference_dict(self.reference)


    def _populate_from_param_dict(self):
        LOGGER.trace('_populate_from_param_dict()')
        self.name = self._get_parameter_value(self._parameter_block,'name')
        self.description = self._get_parameter_value(self._parameter_block,'description')
        self.default = self._get_parameter_value(self._parameter_block,'default')
        self.minItems = self._get_parameter_value(self._parameter_block,'minItems')
        self.minLength = self._get_parameter_value(self._parameter_block,'minLength')
        self.minimum = self._get_parameter_value(self._parameter_block,'minimum')
        self.properties = self._get_parameter_value(self._parameter_block,'properties')
        self.required = self._get_parameter_value(self._parameter_block,'required')
        self.types = self._get_types(self._parameter_block)
        self.uniqueItems = self._get_parameter_value(self._parameter_block,'uniqueItems')
        self.reference = self._get_parameter_value(self._parameter_block, '$ref')        
        if not self.reference:
            items = self._get_parameter_value(self._parameter_block, "items", None)
            if items:
                self.reference = self._get_parameter_value(items, "$ref")

    def _populate_values_from_reference_dict(self, ref_id: str) -> str:
        LOGGER.trace(f'_populate_from_reference_dict({ref_id})')
        values = ""
        ref_block = self._get_reference_id_definition(ref_id)
        LOGGER.debug(f'{ref_block}')
        if ref_block:
            if 'type' not in ref_block:
                if 'items' in ref_block:
                    ref_block = ref_block.get('items')
            
            if 'type' in ref_block:
                r_types = ref_block.get('type')
                if not self.description:
                    self.description = self._get_parameter_value(ref_block, 'description')
                r_enums = []
                if isinstance(r_types, str):
                    if r_types == "string":
                        r_enums = ref_block.get('enums',[])
                        self.types = self._get_types(ref_block)
                    elif r_types == "boolean":
                        r_enums = ['True','False']
                elif isinstance(r_types, list):
                    for r_type in r_types:
                        if isinstance(r_type) is dict:
                            if r_type.get('enums'):
                                r_enums.extend(r_type['enums'])
                            elif r_type.get('type') == 'boolean':
                                r_enums.extend(['True','False'])
                            elif r_type.get('type') == 'integer':
                                r_max = r_type.get('maximum')
                                r_min = r_type.get('minimum')
                                if r_max:
                                    r_enums.extend([f'{r_min}..{r_max}'])
                    r_enums = sorted(set(r_enums)) # unique list
                    values = ', '.join(r_enums)

        return values

    def print_parameter_definition(self):
        print(f'{self.name}')
        self._print_parameter_line('   Desc     ', self.description)
        self._print_parameter_line('   Min Items', self.minItems)
        self._print_parameter_line('   Required ', self.required)
        self._print_parameter_line('   Reference', self.reference)
        # self._print_parameter_line('   Maximum  ', p_max)
        if self.types:
            self._print_types()
        self._print_parameter_line('   UniqItems', self.uniqueItems)
        self._print_parameter_line('   Minimum  ', self.minimum)
        self._print_parameter_line('   Values   ', self.values)
        self._print_parameter_line('   Default  ', self.default)
        print()        


    def _print_types(self):
        indent = 8
        type_list = self.types.split('|')
        type_list = list(filter(None, type_list))
        type_set = sorted(set(type_list)) # Remove duplicates
        caption = '   Type     '
        for p_type in type_set:
            if len(p_type) > self._max_cols - len(caption):
                token = p_type.split('[')
                if len(token) > 1:
                    self._print_parameter_line(caption, token[0])
                    p_type = f'{" "*indent}[{token[1]}'
                    caption = '            '
            self._print_parameter_line(caption, p_type, indent)
            caption = '            '

    def _get_types(self, block_dict: dict) -> str:
        return_type = ""
        LOGGER.trace(f'_get_types() - bloc_dict\n        {block_dict}')
        type_token = self._get_parameter_value(block_dict, "type", "")
        if not type_token and '$ref' in block_dict:
            LOGGER.trace(f'$ref Type refinement: {block_dict}')
            ref_id = block_dict['$ref']
            ref_block = self._get_reference_id_definition(ref_id)
            if ref_block:
                return_type = self._get_types(ref_block)
        else:
            token_type = type(type_token)
            type_caption = f'{type_token}:'
            type_caption = f'{type_caption:7}'
            LOGGER.trace(f'  type_token: {type_token}  token_type: {token_type}  type_caption: {type_caption}')
            if token_type in [ list, dict ]:
                if token_type is list:
                    LOGGER.trace(f'list Type refinement: {block_dict}')
                    return_type = ""
                    for type_entry in type_token:
                        if isinstance(type_entry, str):
                            return_type += f'{type_entry},'
                        else:
                            return_type += f'{self._get_types(type_entry)}|'
                else:
                    LOGGER.trace(f'dict Type refinement: {block_dict}')
                    return_type += f'{self._get_types(type_token)}|'

            elif token_type == str: 
                if type_token == "boolean":
                    LOGGER.trace(f'bool Type refinement: {block_dict}')
                    return_type = f'{type_caption} True,False'

                elif type_token == "integer":
                    LOGGER.trace(f'int Type refinement: {block_dict}')
                    t_max = int(block_dict.get('maximum',-1))
                    t_min = int(block_dict.get('minimum', -1))
                    return_type = type_caption
                    if t_max > 0 and t_min >= 0:
                        return_type = f'{type_caption} ({t_min}..{t_max})'
                    else:
                        return_type = type_token
                # TODO: Handle 'array' type in block dict
                elif 'enum' in block_dict:
                    LOGGER.trace(f'enums Type refinement: {block_dict}')
                    enums = sorted(set(block_dict['enum']))
                    return_type = f"{type_caption} enum [{','.join(enums)}]"
                    # return_type = f"{type_caption} enum"

                else:
                    LOGGER.trace(f'str Type refinement: {block_dict}')
                    if 'additionalProperties' in block_dict:
                        return_type = f"{type_caption} additionalProperties"
                    elif 'items' in block_dict:
                        return_type = f"{type_caption} items"
                    elif 'description' in block_dict:
                        return_type = f'{type_caption} {block_dict["description"]}'
                    elif '$ref' in block_dict:
                        return_type = f'{type_caption} {block_dict["$ref"]}'

                if return_type:
                    if 'default' in block_dict:  # and not self.default:
                        self.default = str(block_dict['default'])
                else:
                    LOGGER.trace(f'NO Type refinement: {block_dict}')
                    return_type = f'{type_caption} {list(block_dict.keys())[0]}'
            else:   
                # TODO: Expand here for type  type(range|min|max|...)
                LOGGER.trace(f'unk Type refinement: {block_dict}')
                return_type = type_token

        if return_type.endswith(','):
            return_type = return_type[:-1]
        LOGGER.trace(f'_get_types() returns: {return_type}')
        return return_type

    def _get_parameter_value(self, p_dict: dict, key: str, default: str = None) -> str:
        token = p_dict.get(key, default)
        # LOGGER.debug(f'_get_parameter_value()  key: {key:15}  dict: {p_dict}')
        return token

    def _get_reference_id_definition(self, ref_id: str) -> str:
        LOGGER.trace(f'_get_reference_id_definition({ref_id})')
        ref_dict = self._reference_block.get(ref_id, None)
        if ref_dict:
            LOGGER.debug(f'Retrieved referenceId: {ref_id}')
        else:
            LOGGER.trace(f'No reference found for: {ref_id}')
        return ref_dict 


    def _print_parameter_line(cls, caption: str, value: str, value_indent: int = 0):
        if value:
            cls._get_console_size()
            sep = ":"
            if len(caption.strip()) == 0:
                sep = " "
            label = f'{caption:13}{sep} '
            # max_len is largest size of value before screen overflow
            max_len = cls._max_cols - len(label)
            print(f'{label}',end='')
            value = str(value)
            while len(value) > max_len:
                idx = value.rfind(",", 0, max_len)
                if idx <= 0:
                    idx = value.rfind(" ",0, max_len)
                if idx <= 0:
                    max_len = len(value)
                else:
                    print(f'{value[0:idx+1]}')
                    value = value[idx+1:].strip()
                    value = f'{" "*value_indent}{value}'
                    print(f"{' '*len(label)}",end='')
            print(value)

    def _get_console_size(cls) -> Tuple[int, int]:
        """Retrieve console size in Rows and Columns"""
        cls._max_rows = int(os.getenv('LINES', -1))
        cls._max_cols = int(os.getenv('COLUMNS', -1))
        if cls._max_rows <= 0 or cls._max_cols <= 0:
            size = os.get_terminal_size()
            cls._max_rows = int(size.lines)
            cls._max_cols = int(size.columns)
        return cls._max_rows, cls._max_cols

class KodiObj():
    CSV_CAPABLE_COMMANDS =  {
        'Addons.GetAddons': 'addons',
        'AudioLibrary.GetAlbums': 'albums',
        'AudioLibrary.GetArtists': 'artists',
        'AudioLibrary.GetGenres': 'genres',
        'AudioLibrary.GetRecentlyAddedAlbums': 'albums',
        'AudioLibrary.GetRecentlyAddedSongs': 'songs',
        'AudioLibrary.GetRecentlyPlayedAlbums': 'albums',
        'AudioLibrary.GetRecentlyPlayedSongs': 'songs',
        'VideoLibrary.GetRecentlyAddedEpisodes': 'episodes' 
        }

    def __init__(self, host: str = "localhost", port: int = 8080, user: str = None, password: str = None, json_loc: str = "./json-defs"):
        LOGGER.debug("KodiObj created")
        self._host = host
        self._ip = self._get_ip(host)
        self._port = port
        self._userid = user
        self._password = password
        self._kodi_api_version = None
        self._namespaces = {}
        self._kodi_references = {}
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

        LOGGER.debug(f'  host: {host}, ip: {self._ip}, port: {port}')
        this_path = pathlib.Path(__file__).absolute().parent
        json_dict_loc = this_path / pathlib.Path(json_loc) / "methods.json"
        LOGGER.debug(f'  Loading method definitionsL {json_dict_loc}')
        all_methods = dict(sorted(self._load_kodi_json_def(json_dict_loc).items()))
        
        last_ns = ""
        for entry, value in all_methods.items():
            token = entry.split('.')
            ns = token[0]
            method = token[1]
            if ns != last_ns:
                self._namespaces[ns] = {}
                last_ns = ns
            self._namespaces[ns][method] = value
            self._namespaces[ns][method]['csv'] = (entry in KodiObj.CSV_CAPABLE_COMMANDS.keys())
        
        json_dict_loc = this_path / pathlib.Path(json_loc) / "types.json"
        LOGGER.debug(f'  Loading reference/types definitions: {json_dict_loc}')
        self._kodi_references = self._load_kodi_json_def(json_dict_loc)

        kodi_version_loc = this_path / pathlib.Path(json_loc) / "version.txt"
        if kodi_version_loc.exists():
            self._kodi_api_version = kodi_version_loc.read_text().replace('\n','')
        else:
            self._kodi_api_version = "Unknown"
        LOGGER.debug(f'  Kodi RPC Version: {self._kodi_api_version}')
        
    def get_namespace_list(self) -> list:
        """Returns a list of the Kodi namespace objeccts"""
        return self._namespaces.keys()
    
    def get_namespace_method_list(self, namespace: str) -> list:
        """Returns a list of the methods for the requested namespace"""
        commands = []
        LOGGER.debug(f'retrieving methods for namespace: {namespace}')
        ns = self._namespaces.get(namespace, None)
        if ns:
            commands = ns.keys()
        return commands
    
    def check_command(self, namespace: str, method: str, parms: str = None) -> bool:
        """Validate namespace method combination, true if valid, false if not"""
        self._clear_response()
        full_namespace = namespace
        if method:
            full_namespace += f".{method}"
        LOGGER.debug(f'Check Command: {full_namespace}')
        if namespace not in self._kodi_references:
            if namespace not in self._namespaces.keys():
                self._set_response(-10, f"Invalid namespace \'{full_namespace}", False)
                LOGGER.error(f'Invalid namespace \'{full_namespace}')
                return False
            if method:
                if method not in self._namespaces[namespace].keys():
                    self._set_response(-20, f'\'{method}\' is not valid method\' for namespace \'{namespace}\'', False)
                    LOGGER.error(f'\'{method}\' is not valid method\' for namespace \'{namespace}\'')
                    return False
            else:
                LOGGER.error(f'Must supply Method for namespace \'{namespace}\'')
                return False

            param_template = self._namespaces[namespace][method]
            if param_template['description'] == "NOT IMPLEMENTED.":
                self._set_response(-30,f'{full_namespace} has not been implemented',False)
                LOGGER.error(f'{full_namespace} has not been implemented')
                return False

        # TODO: Check for required parameters
        LOGGER.debug(f'  {full_namespace} is valid.')
        return True

    def send_request(self, namespace: str, command: str, input_params: dict) -> bool:
        """Send Namesmpace.Method command to target host"""
        LOGGER.trace(f"send_request('{namespace}'),('{command}'),('{input_params}')")
        method = f'{namespace}.{command}'
        LOGGER.debug(f'Load Command Template : {method}')
        param_template = self._namespaces[namespace][command]
        parm_list = param_template['params']
        LOGGER.debug(f'  template:  {param_template}')
        LOGGER.debug(f'  parm_list: {parm_list}')
        req_parms = {}
        LOGGER.trace('  Parameter dictionary:')
        for parm_entry in parm_list:
            parm_name = parm_entry['name']
            parm_value = input_params.get(parm_name, None)
            if parm_value is None:
                parm_value = parm_entry.get('default', None)
            if parm_value is not None:
                if isinstance(parm_value, bool):
                    LOGGER.trace('isBool')
                    req_parms[parm_name] = "true" if parm_value else "false"
                elif isinstance(parm_value, int):
                    req_parms[parm_name] = int(parm_value)
                else:
                    req_parms[parm_name] = parm_value
                LOGGER.trace(f'    Key    : {parm_name:15}  Value: {req_parms[parm_name]} {type(parm_value)}')
            else:
                LOGGER.trace(f'    Key    : {parm_name:15}  Value: {parm_value} BYPASS')
            
        LOGGER.trace('')
        return self._call_kodi(method, req_parms)

    # === Help functions ==========================================================
    def help(self, input_string: str = None):
        """Provide help context for the namespace or namespace.method"""
        namesp = None
        method = None
        ref_id = None
        if input_string:
            if input_string in self._kodi_references:
                ref_id = input_string
            else:
                if "." in input_string:
                    tokens = input_string.split(".")
                    namesp = tokens[0]
                    method = tokens[1]
                else:
                    namesp = input_string

        LOGGER.debug(f'Help - {input_string}')
        LOGGER.debug(f'  Namesapce : {namesp}')
        LOGGER.debug(f'  Method    : {method}')
        LOGGER.debug(f'  RefID     : {ref_id}')

        if ref_id:
            self._help_reference(ref_id)
            return

        if not namesp or (namesp == "help" or namesp == "Help"):
            # General help
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

    def _help_sep_line(self) -> str:
        return f"{'—'*HelpParameter()._max_cols}"


    def _help_namespaces(self):
        LOGGER.trace('_help_namespaces()')
        print("\nKodi namespaces:\n")
        print("   Namespace       Methods")
        print(f"  {'—'*15} {'—'*70}")
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
        LOGGER.trace(f'_help_namespace({ns})')
        ns_commands = self.get_namespace_method_list(ns)

        print(f'\n{ns} Namespace:\n')
        print('  Method                              Description')
        print(f"  {'—'*35} {'—'*50}")
        for token in ns_commands:
            def_block = self._namespaces[ns][token]
            # def_block = json.loads(self._namespaces[ns][token])
            description = def_block['description']
            method = f'{ns}.{token}'
            print(f'  {method:35} {description}')
    
    def _help_namespace_method(self, ns: str, method: str):
        # help_json = json.loads(self._namespaces[ns][method])
        LOGGER.trace(f'_help_namespace_method({ns}, {method})')
        help_json = self._namespaces[ns][method]
        print()
        param_list = help_json.get('params', [])
        p_names = self._get_parameter_names(param_list)
        print(self._help_sep_line())
        HelpParameter()._print_parameter_line("Signature", f'{ns}.{method}({p_names})',)
        # print(f'Signature    : {ns}.{method}({p_names})')
        description = help_json['description']
        if help_json.get('csv'):
            description = f'{description} (csv)'
        HelpParameter()._print_parameter_line("Description", description,)
        print(self._help_sep_line())

        if len(param_list) > 0:
            for param_item in param_list:
                hp = HelpParameter(param_item, self._kodi_references)
                hp.populate()
                hp.print_parameter_definition()

        LOGGER.info(f'\nRaw Json Definition:\n{json.dumps(help_json,indent=2)}')

    def _help_reference(self, ref_id: str):
        LOGGER.trace(f'__help_reference({ref_id})')
        help_json = self._kodi_references.get(ref_id)
        print(self._help_sep_line())
        print(f'Reference: {ref_id}')
        print(f'{json.dumps(help_json,indent=2)}')
        print('')

    # === Private Class Fuctions ==============================================================
    def _get_ip(self, host_name: str) -> str:
        ip = None
        try:
            ip = socket.gethostbyname(host_name)
        except socket.gaierror as sge:
            LOGGER.trace(f'{host_name} cannot be resolved: {repr(sge)}')
        return ip
       
    def _http_client_print(self,*args):
        self._requests_log.debug(" ".join(args))    

    def _load_kodi_json_def(self, file_name: pathlib.Path) -> dict:
        """Load kodi namespace definition from configuration json file"""
        # this_path = os.path.dirname(os.path.abspath(__file__))
        # json_file = f'{this_path}{os.sep}kodi_namespaces.json'
        if not file_name.exists():
            raise FileNotFoundError(file_name)
        with open(file_name,"r") as json_fh:
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
        LOGGER.debug('  Response -')
        LOGGER.debug(f'    status_code: {code}')
        LOGGER.debug(f'    resp_test  : {text}')
        LOGGER.debug(f'    success    : {success}')

    def _call_kodi(self, method: str, params: dict = {}) -> bool:
        self._clear_response()
        MAX_RETRY = 2
        payload = {"jsonrpc": "2.0", "id": 1, "method": f"{method}", "params": params }
        headers = {"Content-type": "application/json"}
        LOGGER.trace(f'Prep call to {self._host}')
        LOGGER.trace(f"  URL    : {self._base_url}")
        LOGGER.trace(f"  Method : {method}")
        LOGGER.trace(f"  Payload: {payload}")

        retry = 0
        success = False  # default for 1st loop cycle
        while not success and retry < MAX_RETRY:
            try:
                LOGGER.trace(f'Making call to {self._base_url} for {method}')
                resp = requests.post(self._base_url,
                                    auth=(self._userid, self._password),
                                    data=json.dumps(payload),
                                    headers=headers, timeout=(5,3)) # connect, read

                if resp.status_code == 200:
                    resp_json = json.loads(resp.text)
                    if 'error' in resp_json.keys():
                        self._set_response(resp_json['error']['code'], resp.text, True)
                    else:
                        self._set_response(0, resp.text, True)
                    success = True
                else:
                    retry = MAX_RETRY
                    resp.raise_for_status()
            except requests.RequestException as re:
                LOGGER.debug(repr(re))
                retry = MAX_RETRY + 1
                self._error_json['error']['code'] = -20
                self._error_json['error']['data']['method'] = method
                self._error_json['error']['message'] = repr(re)
                self._set_response(-20, json.dumps(self._error_json))
            except Exception as ce:
                LOGGER.debug(repr(ce))
                retry += 1
                if not hasattr(ce, "message"):
                    self._error_json['error']['code'] = -30
                    self._error_json['error']['code']['data']['method'] = method
                    self._error_json['error']['message'] = repr(ce)
                    self._set_response(-30, json.dumps(self._error_json))
                time.sleep(2)

        if not success:
            LOGGER.trace(self._error_json)
        return success

    def _get_parameter_names(self, json_param_list: list, identify_optional: bool = True) -> list:
        name_list = []
        for p_entry in json_param_list:
            parameter_name = p_entry['name']
            if p_entry.get('required', False) or not identify_optional:
                name_list.extend([parameter_name])
            else:
                name_list.extend([f"[{parameter_name}]"])
        return ', '.join(name_list)


    # === Parsing (parameter) routines =========================================================
    def _get_types(self, param: dict) -> str:
        param_type = param.get('type', "String")
        return_types = type(param_type)
        LOGGER.debug(f'_get_types for: {param}')
        if isinstance(param_type, str):
            return_types = param_type
        elif isinstance(param_type, list):
            types_list = []
            return_types = ""
            for token_type in param_type:
                if "type" in token_type:
                    types_list.extend([token_type['type']])
                elif "$ref" in token_type:
                    ref_types = self._get_reference_types(token_type)
                    types_list.extend(ref_types.split('|'))

            return_types += '|'.join(list(set(types_list)))
            
        LOGGER.debug(f'_get_types returns: {return_types}')
        return return_types

    def _get_reference_types(self, param: dict) -> str:
        types = None
        ref_dict = self._get_reference_id_definition(param)
        LOGGER.debug(f'_get_reference_types for: {param}')        
        if not ref_dict:
            types = param.get('$ref')
        else:
            r_types = ref_dict['type']
            ret_types = []
            if isinstance(r_types, str):
                ret_types.extend([r_types])
            elif isinstance(r_types, list):
                for r_type in ref_dict['type']:
                    val = r_type.get('type')
                    if not val:
                        val = r_type.get('$ref')
                    ret_types.extend([val])
            types = '|'.join(ret_types)
        
        return types
