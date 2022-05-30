# kodi-cli
Command Line Interface for Kodi

I wanted a CLI for Kodi to be used for automation...  I found a few out there, but none that did what I was looking for exactly...

I didn't want to have to hard-code every command, so I use a json definition file (kodi_namespaces.json) that reflects the commands found at https://kodi.wiki/view/JSON-RPC_API/v12.

Not all the commands are filled in, as I get time I will translate additional ones into the json definition.


```
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
  ```

To list all namespaces:
```
SYNTAX:
  python kodi_cli.py -H KODIHOST -u user -p pwd help

OUTPUT:
  Kodi namespaces:
  ---------------------------
  AddOns
  Application
  AudioLibrary
  Favorites
  GUI
  Input
  JSONRPC
  PVR
  Player
  Playlist
  Profiles
  Settings
  System
  VideoLibrary
```

To list all commands for the Application namespace:
```
SYNTAX:
  python kodi_cli.py -H KODIHOST -u user -p pwd help Application
  or
  python kodi_cli.py -H KODIHOST -u user -p pwd Application

OUTPUT:
  Application namespace commands:

  Method                    Description
  ------------------------- --------------------------------------------
  Application.GetProperties Retrieves the values of the given properties
  Application.Quit          Quit application
  Application.SetMute       Toggle mute/unmute
  Application.SetVolume     Set the current volume
```

To list the syntax for a particular namespace command:
```
SYNTAX:
  python kodi_cli.py -H KODIHOST -u user -p pwd help Application SetMute

OUTPUT:
  Syntax: Application.SetMute
  ------------------------------------------------------
  {
    "description": "Toggle mute/unmute",
    "params": [
      {
        "$ref": "Global.Toggle",
        "name": "mute",
        "required": true
      }
    ],
    "permission": "ControlPlayback",
    "returns": {
      "description": "Mute state",
      "type": "boolean"
    },
    "type": "method"
  }
```

To toggle the mute on
```
SYNTAX:
  python kodi_cli.py -H KODIHOST -u user -p pwd Application SetMute mute=True

```
  Still TODO:
  <ul>
  <li>Create a secrets file so credentials don't have to be suppliled on the cmdline.</li>
  </ul>