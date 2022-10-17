import http.client
import json
import logging
import os
import socket
from sqlite3 import Row

import requests

# TODO:
#   Edit parameters prior to call for cleaner error messages
#   Parse parameter json better

class HelpParameter():
    _max_rows = 0
    _max_cols = 0
    
    def __init__(self, parameter_dict: dict = None, reference_dict: dict = None):
        self._LOGGER = logging.getLogger(__name__)
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
        self._LOGGER.info(f'populate() - block: {self._parameter_block}')
        self._populate_from_param_dict()
        if self.reference:
            self.values = self._populate_from_reference_dict(self.reference)


    def _populate_from_param_dict(self):
        self._LOGGER.info('_populate_from_param_dict()')
        self.name = self._get_parameter_value(self._parameter_block,'name')
        self.description = self._get_parameter_value(self._parameter_block,'description')
        self.default = self._get_parameter_value(self._parameter_block,'default')
        self.minItems = self._get_parameter_value(self._parameter_block,'minItems')
        self.minLength = self._get_parameter_value(self._parameter_block,'minLength')
        self.minimum = self._get_parameter_value(self._parameter_block,'minimum')
        self.properties = self._get_parameter_value(self._parameter_block,'properties')
        self.required = self._get_parameter_value(self._parameter_block,'required')
        type_token = self._get_parameter_value(self._parameter_block,'type')
        self.types = self._get_types(self._parameter_block)
        self.uniqueItems = self._get_parameter_value(self._parameter_block,'uniqueItems')
        self.reference = self._get_parameter_value(self._parameter_block, '$ref')        
        if not self.reference:
            items = self._get_parameter_value(self._parameter_block, "items", None)
            if items:
                self.reference = self._get_parameter_value(items, "$ref")

    def _populate_from_reference_dict(self, ref_id: str) -> str:
        self._LOGGER.info(f'_populate_from_reference_dict({ref_id})')
        values = None
        ref_block = self._get_reference_id_definition(ref_id)
        self._LOGGER.debug(f'{ref_block}')
        if ref_block:
            if 'type' not in ref_block:
                if 'items' in ref_block:
                    ref_block = ref_block.get('items')
            
            if 'type' in ref_block:
                r_types = ref_block.get('type')
                if not self.description:
                    self.description = self._get_parameter_value(ref_block, 'description')
                r_enums = []
                if type(r_types) is str:
                    if r_types == "string":
                        r_enums = ref_block.get('enums',[])
                        self.types = self._get_types(ref_block)
                    elif r_types == "boolean":
                        r_enums = ['True','False']

                elif type(r_types) is list:
                    for r_type in r_types:
                        if r_type.get('enums'):
                            r_enums.extend(r_type['enums'])
                        elif r_type.get('type') == 'boolean':
                            r_enums.extend(['True','False'])
                        elif r_type.get('type') == 'integer':
                            r_max = r_type.get('maximum')
                            r_min = r_type.get('minimum')
                            if r_max:
                                r_enums.extend([f'{r_min}..{r_max}'])
                    values = ', '.join(r_enums)

        return values

    def print_parameter_definition(self):
        print(f'{self.name}')
        self._print_parameter_line('   Desc     ', self.description)
        self._print_parameter_line('   Min Items', self.minItems)
        self._print_parameter_line('   Required ', self.required)
        self._print_parameter_line('   UniqItems', self.uniqueItems)
        self._print_parameter_line('   Minimum  ', self.minimum)
        # self._print_parameter_line('   Maximum  ', p_max)
        if self.types:
            type_list = self.types.split('|')
            type_list = list(filter(None, type_list))
            type_set = set(type_list)
            caption = '   Type     '
            for p_type in type_set:
                self._print_parameter_line(caption, p_type)
                caption = '            '
        self._print_parameter_line('   Reference', self.reference)
        self._print_parameter_line('   Values   ', self.values)
        self._print_parameter_line('   Default  ', self.default)
        print()        


    def _get_types(self, block_dict: dict) -> str:
        return_type = None
        type_token = self._get_parameter_value(block_dict, "type", None)
        self._LOGGER.debug(f'_get_types() - bloc_dict\n    {block_dict}')
        if not type_token and '$ref' in block_dict:
                self._LOGGER.info(f'$ref Type refinement: {block_dict}')
                ref_id = block_dict['$ref']
                ref_block = self._get_reference_id_definition(ref_id)
                if ref_block:
                    return_type = self._get_types(ref_block)
                # values = self._populate_from_reference_dict(ref_id)
        else:
            token_type = type(type_token)
            type_caption = f'{type_token}:'
            type_caption = f'{type_caption:10}'
            self._LOGGER.debug(f'  type_token: {type_token}  token_type: {token_type}  type_caption: {type_caption}')
            if token_type in [ list, dict ]:
                if token_type is list:
                    self._LOGGER.info(f'list Type refinement: {block_dict}')
                    return_type = ""
                    for type_entry in type_token:
                        return_type += f'{self._get_types(type_entry)}|'
                else:
                    self._LOGGER.info(f'dict Type refinement: {block_dict}')
                    return_type += f'{self._get_types(type_token)}|'
            elif token_type == str: 
                if type_token == "boolean":
                    self._LOGGER.info(f'bool Type refinement: {block_dict}')
                    return_type = f'{type_caption} True,False'
                elif type_token == "integer":
                    self._LOGGER.info(f'int Type refinement: {block_dict}')
                    t_max = int(block_dict.get('maximum',-1))
                    t_min = int(block_dict.get('minimum', -1))
                    return_type = type_caption
                    if t_max > 0 and t_min >= 0:
                        return_type = f'{type_caption} ({t_min}..{t_max})'
                    else:
                        return_type = type_token
                elif 'enums' in block_dict:
                    self._LOGGER.info(f'enums Type refinement: {block_dict}')
                    enums = block_dict['enums']
                    return_type = f"{type_caption} enum [{','.join(enums)}]"
                    # return_type = f"{type_caption} enum"
                else:
                    self._LOGGER.info(f'str Type refinement: {block_dict}')
                    if 'additionalProperties' in block_dict:
                        if 'properties' in block_dict:
                            return_type = f'{type_caption} {list(block_dict["properties"].keys())[0]}'
                        elif 'type' in block_dict:
                            return_type = f'{type_caption} {list(block_dict.keys())[0]}'                  
                    elif 'description' in block_dict:
                        return_type = f'{type_caption} {block_dict["description"]}'
                    elif '$ref' in block_dict:
                        return_type = f'{type_caption} {block_dict["$ref"]}'
                if not return_type:
                    self._LOGGER.info(f'NO Type refinement: {block_dict}')
                    return_type = f'{type_caption} {list(block_dict.keys())[0]}'
            else:   
                # TODO: Expand here for type  type(range|min|max|...)
                self._LOGGER.info(f'unk Type refinement: {block_dict}')
                return_type = type_token

        return return_type

    def _get_parameter_value(self, p_dict: dict, key: str, default: str = None) -> str:
        token = p_dict.get(key, default)
        # self._LOGGER.debug(f'_get_parameter_value()  key: {key:15}  dict: {p_dict}')
        return token

    def _get_reference_id_definition(self, ref_id: str) -> str:
        self._LOGGER.info(f'_get_reference_id_definition({ref_id})')
        ref_dict = self._reference_block.get(ref_id, None)
        if ref_dict:
            self._LOGGER.debug(f'Retrieved referenceId: {ref_id}')
        else:
            self._LOGGER.info(f'No reference found for: {ref_id}')
        return ref_dict 


    def _print_parameter_line(cls, caption: str, value: str):
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
                    print(f"{' '*len(label)}",end='')
            print(value)

    def _get_console_size(cls):
        """Return console size in Rows and Columns"""
        cls._max_rows = int(os.getenv('LINES', -1))
        cls._max_cols = int(os.getenv('COLUMNS', -1))
        if cls._max_rows <= 0 or cls._max_cols <= 0:
            size = os.get_terminal_size()
            cls._max_rows = int(size.lines)
            cls._max_cols = int(size.columns)

class KodiObj():
    def __init__(self, host: str = "localhost", port: int = 8080, user: str = None, password: str = None):
        self._LOGGER = logging.getLogger(__name__)
        self._LOGGER.debug("KodiObj created")
        self._host = host
        self._ip = self._get_ip(host)
        self._port = port
        self._userid = user
        self._password = password
        self._LOGGER.debug(f'  host: {host}, ip: {self._ip}, port: {port}')
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

        if self._LOGGER.getEffectiveLevel() == logging.DEBUG:
            self._LOGGER.debug('HTTP Logging enabled.')
            http.client.HTTPConnection.debuglevel = 1
            # urllib_log = logging.getLogger('urllib3')
            # urllib_log.setLevel(logging.DEBUG)
            self._requests_log = logging.getLogger("requests.packages.urllib3")
            self._requests_log.setLevel(logging.DEBUG)
            self._requests_log.propagate = True
            http.client.print = self._http_client_print
        
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
    
    def check_command(self, namespace: str, method: str, parms: str = None) -> bool:
        """Validate namespace method combination, true if valid, false if not"""
        full_namespace = namespace
        if method:
            full_namespace += f".{method}"
        self._LOGGER.debug(f'Check Command: {full_namespace}')
        if namespace not in self._kodi_references:
            if namespace not in self._namespaces.keys():
                self._LOGGER.error(f'Invalid namespace \'{full_namespace}')
                return False
            if method:
                if method not in self._namespaces[namespace].keys():
                    self._LOGGER.error(f'\'{method}\' is not valid method\' for namespace \'{namespace}\'')
                    return False
            else:
                self._LOGGER.error(f'Must supply Method for namespace \'{namespace}\'')
                return False

            param_template = self._namespaces[namespace][method]
            if param_template['description'] == "NOT IMPLEMENTED.":
                self._LOGGER.error(f'{full_namespace} has not been implemented')
                return False

        # TODO: Check for required parameters
        self._LOGGER.debug(f'  {full_namespace} is valid.')
        return True

    def send_request(self, namespace: str, command: str, input_params: dict) -> bool:
        """Send Namesmpace.Method command to target host"""
        method = f'{namespace}.{command}'
        self._LOGGER.debug(f'Load Command Template : {method}')
        param_template = self._namespaces[namespace][command]
        parm_list = param_template['params']
        self._LOGGER.debug(f'  template:  {param_template}')
        self._LOGGER.debug(f'  parm_list: {parm_list}')
        req_parms = {}
        self._LOGGER.info('  Parameter dictionary:')
        for parm_entry in parm_list:
            parm_name = parm_entry['name']
            parm_value = input_params.get(parm_name,None)
            if not parm_value:
                parm_value = parm_entry.get('default', None)
            self._LOGGER.info(f'    Key    : {parm_name:15}  Value: {parm_value}')
            req_parms[parm_name] = parm_value
        self._LOGGER.info('')
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

        self._LOGGER.debug(f'Help - {input_string}')
        self._LOGGER.debug(f'  Namesapce : {namesp}')
        self._LOGGER.debug(f'  Method    : {method}')
        self._LOGGER.debug(f'  RefID     : {ref_id}')

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
        self._LOGGER.info('_help_namespaces()')
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
        self._LOGGER.info(f'_help_namespace({ns})')
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
        self._LOGGER.info(f'_help_namespace_method({ns}, {method})')
        help_json = self._namespaces[ns][method]
        print()
        param_list = help_json.get('params', [])
        p_names = self._get_parameter_names(param_list)
        print(self._help_sep_line())
        print(f'Signature    : {ns}.{method}({p_names})')
        HelpParameter()._print_parameter_line("Description", help_json['description'])
        print(self._help_sep_line())

        if len(param_list) > 0:
            for param_item in param_list:
                hp = HelpParameter(param_item, self._kodi_references)
                hp.populate()
                hp.print_parameter_definition()

        self._LOGGER.debug(f'\nRaw Json Definition:\n{json.dumps(help_json,indent=2)}')

    def _help_reference(self, ref_id: str):
        self._LOGGER.info(f'__help_reference({ref_id})')
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
            self._LOGGER.info(f'{host_name} cannot be resolved: {repr(sge)}')
        return ip
       
    def _http_client_print(self,*args):
        self._requests_log.debug(" ".join(args))    

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
        self._LOGGER.debug('  Response -')
        self._LOGGER.debug(f'    status_code: {code}')
        self._LOGGER.debug(f'    resp_test  : {text}')
        self._LOGGER.debug(f'    success    : {success}')

    def _call_kodi(self, method: str, params: dict = {}) -> bool:
        self._clear_response()
        MAX_RETRY = 2
        payload = {"jsonrpc": "2.0", "id": 1, "method": f"{method}", "params": params }
        headers = {"Content-type": "application/json"}
        self._LOGGER.info(f'Prep call to {self._host}')
        self._LOGGER.info(f"  URL    : {self._base_url}")
        self._LOGGER.info(f"  Method : {method}")
        self._LOGGER.info(f"  Payload: {payload}")

        retry = 0
        success = False  # default for 1st loop cycle
        while not success and retry < MAX_RETRY:
            try:
                self._LOGGER.info(f'Making call to {self._base_url} for {method}')
                resp = requests.post(self._base_url,
                                    auth=(self._userid, self._password),
                                    data=json.dumps(payload),
                                    headers=headers, timeout=(5,3)) # connect, read
                resp_json = json.loads(resp.text)
                if 'error' in resp_json.keys():
                    self._set_response(resp_json['error']['code'], resp.text, True)
                else:
                    self._set_response(0, resp.text, True)
                success = True
            except requests.RequestException as re:
                self._LOGGER.debug(repr(re))
                retry = MAX_RETRY + 1
                self._error_json['error']['code'] = -20
                self._error_json['error']['data']['method'] = method
                self._error_json['error']['message'] = repr(re)
                self._set_response(-20, json.dumps(self._error_json))
            except Exception as ce:
                self._LOGGER.debug(repr(ce))
                retry += 1
                if not hasattr(ce, "message"):
                    self._error_json['error']['code'] = -30
                    self._error_json['error']['code']['data']['method'] = method
                    self._error_json['error']['message'] = repr(ce)
                    self._set_response(-30, json.dumps(self._error_json))
                time.sleep(2)

        return success

    def _get_parameter_names(self, json_param_list: list, identify_optional: bool = True) -> list:
        name_list = []
        for p_entry in json_param_list:
            parameter_name = p_entry['name']
            if p_entry.get('required', False) == True or not identify_optional:
                name_list.extend([parameter_name])
            else:
                name_list.extend([f"[{parameter_name}]"])
        return ', '.join(name_list)


    # === Parsing (parameter) routines =========================================================
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
        if not ref_dict:
            types = param.get('$ref')
        else:
            r_types = ref_dict['type']
            ret_types = []
            if type(r_types) is str:
                ret_types.extend([r_types])
            elif type(r_types) is list:
                for r_type in ref_dict['type']:
                    val = r_type.get('type')
                    if not val:
                        val = r_type.get('$ref')
                    ret_types.extend([val])
            types = '|'.join(ret_types)
        
        return types

    # def _get_reference_values(self, param: dict) -> str:
    #     values = None
    #     ref_dict = self._get_reference_id_definition(param)
    #     if not ref_dict:
    #         ref_dict = param
    #     if ref_dict:
    #         if ref_dict.get('items'):
    #             ref_dict = ref_dict.get('items')
    #         r_types = ref_dict.get('type')
    #         self._LOGGER.debug(f'r_types: {r_types} - type: {type(r_types)}')
    #         r_enums = []
    #         if type(r_types) is str:
    #             r_enums = ref_dict.get('enums',[])
    #         elif type(r_types) is list:
    #             for r_type in ref_dict['type']:
    #                 if r_type.get('enums'):
    #                     r_enums.extend(r_type['enums'])
    #                 elif r_type.get('type') == 'boolean':
    #                     r_enums.extend([ 'True', 'False' ])
    #                 elif r_type.get('type') == 'integer':
    #                     r_max = r_type.get('maximum')
    #                     r_min = r_type.get('minimum')
    #                     if r_max:
    #                         r_enums.extend([f'{r_min}..{r_max}'])

    #         values = ','.join(r_enums)

    #     return values

    # def _get_reference_id_definition(self, param: dict) -> str:
    #     id = param.get('$ref')
    #     ref_dict = self._kodi_references.get(id)
    #     if ref_dict:
    #         self._LOGGER.debug(f'Retrieved referenceId: {id}')
    #     else:
    #         self._LOGGER.debug(f'No reference found for: {id}')
    #     return ref_dict 
