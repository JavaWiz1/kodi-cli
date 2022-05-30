# kodi-cli
Command Line Interface for Kodi

usage: kodi_cli.py [-h] -H HOST [-P PORT] [-u USER] [-p PASSWORD] [-v] [command [command ...]]

positional arguments:
  command               RPC command cmd.sub-cmd (help namespace to list)

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Kodi hostname
  -P PORT, --port PORT  Kodi RPC listen port
  -u USER, --user USER  Kodi authenticaetion username
  -p PASSWORD, --password PASSWORD
                        Kodi autentication password
  -v, --verbose         Turn out verbose output, more parms increase verbosity