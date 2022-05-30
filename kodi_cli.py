import json
import argparse
import requests
import logging

LOGGER = logging.getLevelName(__name__)
# TODO: Create secrets file that is read on starup if exists

class KodiObj():
    def __init__(self, host: str, port: int, user: str, password: str):
        self._host = host
        self._port = port
        self._userid = user
        self._password = password
        self._namespaces = self._load_kodi_namespaces()
        self._base_url = f'http://{host}:{port}/jsonrpc'
        self._LOGGER = logging.getLogger(__name__)
        self._LOGGER.info("KodiObj created")

    def _load_kodi_namespaces(self) -> dict:
        with open("./kodi_namespaces.json","r") as json_fh:
            json_data = json.load(json_fh)
        return json_data

    def get_namespace_list(self) -> list:
        return self._namespaces.keys()
    
    def get_namespace_command_list(self, namespace: str) -> list:
        commands = []
        ns = self._namespaces.get(namespace, None)
        if ns:
            commands = ns.keys()
        return commands
    
    def check_command(self, namespace: str, command: str) -> bool:
        if namespace not in self._namespaces.keys():
            self._LOGGER.error(f'Invalid namespace: {namespace}')
            return False
        if command not in self._namespaces[namespace].keys():
            self._LOGGER.error(f'{command} is not valid for {namespace}')
            return False
        param_template = json.loads(self._namespaces[namespace][command])
        if param_template['description'] == "NOT IMPLEMENTED.":
            self._LOGGER.error(f'{namespace}.{command} has not been implemented')
            return False
        return True

    def send_request(self, namespace: str, command: str, input_params: dict) -> bool:
        method = f'{namespace}.{command}'
        self._LOGGER.info(f'load param template for: {method}')
        param_template = json.loads(self._namespaces[namespace][command])
        parm_list = param_template['params']
        self._LOGGER.debug(f'  template:  {param_template}')
        self._LOGGER.debug(f'  parm_list: {parm_list}')
        req_parms = {}
        self._LOGGER.info('build parameter dictionary')
        for parm_entry in parm_list:
            parm_name = parm_entry['name']
            parm_value = input_params.get(parm_name,None)
            if not parm_value:
                parm_value = parm_entry.get('default', None)
            self._LOGGER.info(f'  Key    : {parm_name:15}  Value: {parm_value}')
            req_parms[parm_name] = parm_value
        return self._call_kodi(method, req_parms)

    def _clear_response(self):
        self.response_text = None
        self.response_status_code = None
        self.request_success = False

    def _set_response(self, code: int, text: str, success: bool = False):
        self.response_status_code = code
        self.response_text = text
        self.request_success = success

    def _call_kodi(self, method: str, params: dict = {}) -> bool:
        self._clear_response()
        MAX_RETRY = 2
        payload = {"jsonrpc": "2.0", "id": 1, "method": f"{method}", "params": params }
        headers = {"Content-type": "application/json"}
        self._LOGGER.debug(f"URL: {self._base_url}")
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
                success = True
                self._LOGGER.info(f"{self._host}: {resp.status_code} - {resp.text}")
            except requests.RequestException as re:
                retry = MAX_RETRY + 1
                self._set_response(-2, f'{{"result": "{re.__class__.__name__}"}}')
            except Exception as ce:
                retry += 1
                if not hasattr(ce, "message"):
                    self._set_response(-2, json.dumps({"result": repr(ce)}))
                    self._LOGGER.error(f'Exception{retry}: {resp}')
                time.sleep(2)

        if success:
            self._set_response(resp.status_code, resp.text, True)

        # print(f"  [{self.request_success}] ({self.response_status_code}) {self.response_text}")
        return success

    def _help_namespaces(self):
        print("Kodi namespaces -\n")
        print("   Namespace       Methods")
        print("   --------------- ----------------------------------------------------------------------------")
        for ns in self.get_namespace_list():
            methods = ""
            for method in self.get_namespace_command_list(ns):
                if len(methods) == 0:
                    methods = method
                elif len(methods) > 40:
                    print(f'   {ns:15} {methods},')
                    ns = ""
                    methods = method
                else:
                    methods = f"{methods}, {method}"
            print(f'   {ns:15} {methods}\n')

    def _help_namespace(self, ns: str):
        ns_commands = self.get_namespace_command_list(ns)

        print(f'{ns} namespace commands-\n')
        print('  Method                    Description')
        print('  ------------------------- --------------------------------------------')
        for token in ns_commands:
            def_block = json.loads(self._namespaces[ns][token])
            description = def_block['description']
            method = f'{ns}.{token}'
            print(f'  {method:25} {description}')

    def _help_namespace_method(self, ns: str, method: str):
        help_text = json.loads(self._namespaces[ns][method])
        print(f'Syntax: {ns}.{method}')
        print('------------------------------------------------------')
        print(f'{json.dumps(help_text,indent=2)}')

    def help(self, tokens: list = None):
        namesp = None
        method = None

        if tokens:
            if isinstance(tokens, str):
                namesp = tokens
            else:
                namesp = tokens[0]
                if len(tokens) > 1:
                    method = tokens[1]

        if not namesp or (namesp == "help" and method == "namespaces"):
            self._help_namespaces()
            return

        if namesp not in self._namespaces.keys():
            print(f'Unknown namespace [{namesp}]. Try help namespaces')
            return

        if not method:
            self._help_namespace(namesp)
            return
        
        if method not in self.get_namespace_command_list(namesp):
            print(f'Unknown command [{method}] in namespace {namesp}')
            return

        self._help_namespace_method(namesp, method)

def is_integer(token: str) -> bool:
    is_int = True
    try:
        int(token)
    except ValueError:
        is_int = False
    return is_int

def is_boolean(token: str) -> bool:
    is_bool = False
    if token in ["True", "true", "False", "false"]:
        is_bool = True
    # try:
    #     bool(token)
    # except ValueError:
    #     is_bool = False
    return is_bool
def is_list(token: str) -> bool:
    is_list = False
    if token.startswith("[") and token.endswith("]"):
        is_list = True
    return is_list

def make_list_from_string(token: str) -> list:
    text = token[1:-1]
    return text.split(",")

def parse_input(args: list) -> (str, str, dict):
    cmd = None
    sub_cmd = None
    parm_kwargs = {}
    if len(args) > 0:
        cmd = args[0]
        if len(args) > 1:
            sub_cmd = args[1]
            if len(args) > 2:
                parm_kwargs = {}
                for parm_block in args[2:]:
                    token = parm_block.split("=")
                    if len(token) > 1:
                        if is_list(token[1]):
                            parm_kwargs[token[0]] = make_list_from_string(token[1])
                        elif is_integer(token[1]):
                            parm_kwargs[token[0]] = int(token[1])
                        elif is_boolean(token[1]):
                            parm_kwargs[token[0]] = bool(token[1])
                        else:
                            parm_kwargs[token[0]] = token[1]


    return cmd, sub_cmd, parm_kwargs

def setup_logging(log_level):
    lg_format='[%(levelname)-5s] %(message)s'
    logging.basicConfig(format=lg_format, level=log_level,)

def main():
    # -H --host
    # -P --port
    parser = argparse.ArgumentParser()
    parser.add_argument("-H","--host", type=str, help="Kodi hostname", required=True)
    parser.add_argument("-P","--port", type=int, default=8080, help="Kodi RPC listen port")
    parser.add_argument("-u","--user", type=str, default='kodi', help="Kodi authenticaetion username")
    parser.add_argument("-p","--password", type=str, default='kodi', help="Kodi autentication password")
    parser.add_argument("-f","--format", action="store_true", help="Format json output")
    parser.add_argument("-v","--verbose", action='count', help="Turn out verbose output, more parms increase verbosity")
    parser.add_argument("command", type=str, nargs='*', help="RPC command  cmd.sub-cmd (help namespace to list)")
    args = parser.parse_args()
    
    loglvl = logging.ERROR
    if args.verbose:
        if args.verbose == 1:
            loglvl = logging.INFO
        elif args.verbose > 1:
            loglvl=logging.DEBUG
    
    setup_logging(loglvl)
    LOGGER = logging.getLogger(__name__)

    kodi = KodiObj(args.host, args.port, args.user, args.password)
    if not args.command:
        kodi.help()
    elif args.command[0].lower() == "help":
        kodi.help(args.command[1:])
    else:        
        cmd, sub_cmd, params = parse_input(args.command)
        if not sub_cmd:
            kodi.help(cmd)
        elif kodi.check_command(cmd, sub_cmd):
            kodi.send_request(cmd, sub_cmd, params)
            response = kodi.response_text
            if args.format:
                response = json.dumps(json.loads(kodi.response_text), indent=2)
            print(response)

if __name__ == "__main__":
    main()