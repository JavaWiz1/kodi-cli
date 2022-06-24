import json
import logging
import os

import requests

# TODO:
#   Edit parameters prior to call for cleaner error messages
#   Parse parameter json better

class KodiObj():
    def __init__(self, host: str = "localhost", port: int = 8080, user: str = None, password: str = None):
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
    
    def check_command(self, namespace: str, method: str, parms: str = None) -> bool:
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

        # param_template = json.loads(self._namespaces[namespace][method])
        param_template = self._namespaces[namespace][method]
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
        # param_template = json.loads(self._namespaces[namespace][command])
        param_template = self._namespaces[namespace][command]
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

    # === Help functions ==========================================================
    def help(self, input_string: str = None):
        """Provide help context for the namespace or namespace.method"""
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

    def _help_namespaces(self):
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
        help_json = self._namespaces[ns][method]
        print()
        p_names = self._get_parameter_names(help_json.get('params',[]))
        print(f"{'—'*80}")
        print(f'Signature   : {ns}.{method}({p_names})')
        print(f'Description : {help_json["description"]}')

        if len(help_json.get('params',[])) > 0:
            print(f"{'—'*80}")
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
                resp = requests.post(self._base_url,
                                    auth=(self._userid, self._password),
                                    data=json.dumps(payload),
                                    headers=headers, timeout=(5,3)) # connect, read
                success = True
                #self._LOGGER.debug(f"{self._host}: {resp.status_code} - {resp.text}")
            except requests.RequestException as re:
                retry = MAX_RETRY + 1
                self._error_json['error']['code'] = -20
                self._error_json['error']['data']['method'] = method
                self._error_json['error']['message'] = repr(re)
                self._set_response(-20, json.dumps(self._error_json))
            except Exception as ce:
                retry += 1
                if not hasattr(ce, "message"):
                    self._error_json['error']['code'] = -30
                    self._error_json['error']['code']['data']['method'] = method
                    self._error_json['error']['message'] = repr(ce)
                    self._set_response(-30, json.dumps(self._error_json))
                    self._LOGGER.error(f'Exception{retry}: {resp}')
                time.sleep(2)

        if success:
            resp_json = json.loads(resp.text)
            if 'error' in resp_json.keys():
                self._set_response(resp_json['error']['code'], resp.text, True)
            else:
                self._set_response(0, resp.text, True)

        # print(f"  [{self.request_success}] ({self.response_status_code}) {self.response_text}")
        return success


    # ==== Parameter functions =================================================================
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

    def _print_parameter_line(self, caption: str, value: str):
        if value:
            print(f'   {caption:9}: {value}')


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
