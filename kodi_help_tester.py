import sys

from kodi_interface import KodiObj

    
def get_input(prompt: str = "> ", choices: list = [], required = False) -> str:
    ret_val = input(prompt)
    if choices:
        while ret_val not in choices:
            print(f'Invalid selection. Valid entries: {"/".join(choices)}')
            ret_val = input(prompt)
    elif required:
        while not ret_val:
            print('You MUST enter a value.')
            ret_val = input(prompt)

    return ret_val

# def setup_logging(log_level = logging.ERROR):
#     lg_format='[%(levelname)-5s] %(message)s'
#     logging.basicConfig(format=lg_format, level=log_level,)

# def set_loglevel(log_level:str):
#     if log_level == "E":
#         lg_lvl = logging.ERROR
#     elif log_level == "I":
#         lg_lvl = logging.INFO
#     else:
#         lg_lvl = logging.DEBUG
#     logging.getLogger().setLevel(lg_lvl)

def dump_methods(kodi: KodiObj):
    namespaces = kodi.get_namespace_list()
    for ns in namespaces:
        resp = get_input(f"Display: {ns} (y|n|q)> ",['y','n','Y','N','Q','q']).lower()
        if resp == "q":
            break
        elif resp == 'y':
            ns_methods = kodi.get_namespace_method_list(ns)
            for method in ns_methods:
                resp = get_input(f'{ns}.{method} (E,I,D,n,q)> ',['E','I','D','y','n','q',''])
                if resp in ['E','I','D']:
                    # set_loglevel(resp)
                    pass
                elif resp == 'q':
                    sys.exit()
                elif resp == 'n':
                    break
                cmd = f'{ns}.{method}'
                print(cmd)
                kodi.help(cmd)
                print()
                print('\n=========================================================================')

def main():
    # setup_logging()
    # log_level = "E"
    # set_loglevel(log_level)

    kodi = KodiObj()
    # kodi.help("")
    # pause()
    # kodi.help("Application")
    # pause()
    # kodi.help('AudioLibrary.GetArtists')
    dump_methods(kodi)

if __name__ == "__main__":
    main()
