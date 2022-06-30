
import logging

from kodi_interface import KodiObj

LOGGING = logging.getLogger(__name__)


def pause():
    input('Any key to continue...')
    print()
    
def get_input(prompt: str = "> ", choices: list = [], required = False) -> str:
    ret_val = input(prompt)
    if choices:
        while not ret_val in choices:
            print(f'Invalid selection. Valid entries: {"/".join(choices)}')
            ret_val = input(prompt)
    elif required:
        while not ret_val:
            print('You MUST enter a value.')
            ret_val = input(prompt)

    return ret_val

def setup_logging(log_level = logging.ERROR):
    lg_format='[%(levelname)-5s] %(message)s'
    logging.basicConfig(format=lg_format, level=log_level,)

def dump_methods(kodi: KodiObj):
    namespaces = kodi.get_namespace_list()
    for ns in namespaces:
        resp = get_input(f"{ns}> ",['y','n','Y','N','Q','q']).lower()
        if resp == "q":
            break
        elif resp == 'y':
            ns_methods = kodi.get_namespace_method_list(ns)
            for method in ns_methods:
                cmd = f'{ns}.{method}'
                print(cmd)
                kodi.help(cmd)
                print()
                pause()
                print('\n=========================================================================')

def main():
    setup_logging(logging.INFO)
    kodi = KodiObj()
    # kodi.help("")
    # pause()
    # kodi.help("Application")
    # pause()
    # kodi.help('AudioLibrary.GetArtists')
    dump_methods(kodi)

if __name__ == "__main__":
    main()