# kodi-cli

## Command Line Interface for Kodi

This tool can be used from the command line to execute commands against a target Kodi host via the RPC interface defined at  https://kodi.wiki/view/JSON-RPC_API/v12.  

The available commands are defined via jsons files ([**methods.json and types.json**](https://github.com/JavaWiz1/kodi-cli/blob/develop/json-defs/)) which describes all the namespaces, methods, parameters (methods.json) and reference types (types.json) for managing the kodi device remotely. These files are copied from the kodi source repository for kodi v19 (matrix).

**Note** 
- Namespace Methods and Types are case-sensitive.  Use help parameter or refer to the [Kodi RPC page](https://kodi.wiki/view/JSON-RPC_API/v12) for proper capitalization.
- An *entrypoint* is created on install that allows the script to be run without specifying ***python kodi_cli.py***, simply type ***kodi-cli*** to execute the script.
</br></br>
The documentation will reflect calls using the entrypoint (*kodi-cli*) as described above.



</br>

---
## Overall Description

*Commands* are based on Kodi **namespaces, methods and parameters**.  Each namespace (i.e. Application, System,...) has a set of pre-defned methods.  When executing a command you supply the **Namespace.Method parameter(s)** (case-sensitive).

For example, to display the mute and volume level settings on host kodi001, the command is constructed as follows:<br>

  `kodi-cli -H kodi001 -f Application.GetProperties properties=[muted,volume]`
- **-H kodi001** identifies the target host
- **-f** indicates the output should be formatted
- **Application.GetProperties** is the parameter
    - *Application* is the namespace
    - *GetProperties* is the method
    - *properties=[muted,volume]* are the parameters

The output of the tool is the json response from the Kodi endpoint the command was targeted to.
```
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "muted": false,
    "volume": 100
  }
}
```

When defining an object type parameter, create it as a pseudo dictionary as below:

  `kodi-cli -H kodi001 Addons.GetAddons properties=[name,version,summary] limits={start:0,end:99}`
 
 - **limits** is an object, that contains two values start and end.
## Some terms:

| Term | Description |
| ------------- | ---------------------------- |
| namespace | The data model is split into namespace components which can be called via the API |
| methods | Each namespace has a number of methods which perform some function within that namespace |
| parameter(s) | Each namespace.method command may have required or optional parameters to control the output |
| command | A command is a namespace, method, parameter combiniation used to control Kodi function (fmt: Namespace.Method) |
</br>

Parameters can be one of the following types:

- string (default)
- boolean (true / false)
- integer
- list (`[ ... , ... ]`)
- dict (`{ key: value, ... }`)

---

## Usage

```
usage: kodi-cli [-h] [-H HOST] [-P PORT] [-u USER] [-p PASSWORD] [-C] [-f] [-v] [-i] [command [parameter ...]]

Kodi CLI controller v0.2.1

positional arguments:
  command                   RPC command namespace.method (help namespace to list)

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Kodi hostname
  -P PORT, --port PORT  Kodi RPC listen port
  -u USER, --kodi-user USER  
                        Kodi authenticaetion username
  -p PASSWORD, --kodi-password PASSWORD
                        Kodi autentication password
  -C, --create_config   Create empty config
  -CO, --create_config_overwrite
                        Create default config, overwrite if exists
  -f, --format_output   Format json output
  -c, --csv-output      Format csv output (only specific commands)
  -v, --verbose         Verbose output, -v = INFO, -vv = DEBUG
  -i, --info            display program info and quit
```
<br>

**TIPS - When calling the script:**
| action | description |
| ------ | ----------- |
| add -h option | to display script syntax and list of option parameters |
| enter help | as a parameter for help on namespace or namespace.method or namespace.type <br>add -v to get json defintion|
| add -i | to output runtime and program information |
| add -f | to format the json output into a friendly format |
| add -C or (-CO) | to create a config file with runtime defaults (see "Create config file to store defaults" below)|
</br>

**Help commands:**
You can get help from the command line to view namespaces, namespace methods and calling requirements. 

Help Examples
| action | example |
| ------ | ------- |
| list of namespaces |    `kodi-cli help` |
| Methods for Namespace | `kodi-cli Application help` |
| Parameters for Method | `kodi-cli Application.GetProperties help` |
| Type/References | `kodi-cli List.Filter.Albums` to get the type defintion for the reference |

Details for namespaces, methods and type parameters may be found at https://kodi.wiki/view/JSON-RPC_API/v12
 
</br>

---
## Prerequsites:

**Python 3.7+**<br>
**Python packages**
- requests package
- loguru
<br>
Code can be installed via pip or [pipx](https://github.com/pypa/pipx):
- pip install kodi-cli [--user]
- [pipx](https://github.com/pypa/pipx) install kodi-cli

**Kodi configuration**
- Remote control via HTTP must be enabled.
- Enable in Kodi UI - Settings -> Services -> Control
</br></br>

---
## Usage Examples
---
### Create a config file to store defaults
To minimize command-line entry, you can store defaults in a config file which will default values on startup.  The
values can be over-ridded at run-time by providing the optional command-line argument.

To create a default config file, type your standard defaults as if you were going to execute the CLI and add -C (or -CO)
at the end.
The config file will be written with the values.
```
SYNTAX:
  kodi-cli -u myId -p myPassword -P 8080 -C

OUTPUT:
  a file kodi_cli.cfg will be written as:
...
[LOGGING]
logging_enabled = False
logging_filename = ./logs/kodi_cli.log
logging_rotation = 1 MB
logging_retention = 3
logging_level = INFO
logger_blacklist = 

[SERVER]
host = localhost
port = 8080

[LOGIN]
kodi_user = kodi
kodi_pw = kodi

[OUTPUT]
format_output = False
csv_output = False
```
NOTE:
- if current file does not exist, it will be created as ~/.kodi_cli/kodi_cli.cfg
- if current file does exist error will be thrown unless -CO option is used.
- user and password is stored in clear text
</br></br>

---
### List all **namespaces**

Namespaces are modules in Kodi, each namespace manages differ aspects of the Kodi interface

```
SYNTAX:
  kodi-cli help

OUTPUT:

  Kodi namespaces -
    Namespace       Methods
    --------------- ----------------------------------------------------------------------------
    Addons          ExecuteAddon, GetAddonDetails, GetAddons, SetAddonEnabled

    Application     GetProperties, Quit, SetMute, SetVolume

    AudioLibrary    Clean, GetAlbumDetails, GetAlbums, GetArtistDetails,
                    GetArtists, Scan

    Favorites       AddFavorite, GetFavorites

    GUI             ActivateWindow, ShowNotification

    Input           Back, ButtonEvent, ContextMenu, Down, ExecuteAction,
                    Home, Info, Left, Right, Select, SendText,
                    ShowCodec, ShowOSD, ShowPlayProcessInfo, Up
    ...
```
</br></br>

---
### List all namespace ***methods***

Each namespace has a number of methods that can be called.  

To get a list of supported of supported methods for the ***Application*** namespace

```
SYNTAX:
  kodi-cli Application help
  or
  kodi-cli Application

OUTPUT:

  Application Namespace Methods:

  Method                    Description
  ------------------------- --------------------------------------------
  Application.GetProperties Retrieves the values of the given properties
  Application.Quit          Quit application
  Application.SetMute       Toggle mute/unmute
  Application.SetVolume     Set the current volume
```
</br></br>

---
### List the ***method calling signature*** for a namespace method

List the sytax for the Application.SetMute command

```
————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
Signature    : Application.SetMute(mute)
Description  : Toggle mute/unmute
————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
mute
   Required  : True
   Reference : Global.Toggle
   Type      : boolean: True,False
               string: enum [toggle]
   Values    : True, False

```
To use:
``` kodi-cli -H kodi001 Application.SetMute mute=toggle ```

</br></br>

---
## Command Execution Examples

### Toggle Mute on/off

To toggle the mute on, then off

First call will toggle mute on, 2nd call will toggle mute off.

```
SYNTAX:
  kodi-cli -H ServerName Application.SetMute mute=toggle

OUTPUT:
  kodi-cli -H MyKodiServer Application.SetMute mute=toggle
  {"id":1,"jsonrpc":"2.0","result":true}

  kodi-cli -H MyKodiServer Application.SetMute mute=toggle
  {"id":1,"jsonrpc":"2.0","result":false}
```
</br></br>

---
### Retrieve Application Properties

To retrieve the muted status and volume level for server kodi001
```
SYNTAX:
  kodi-cli -H kodi001 Application.GetProperties properties=[muted,volume] -f

OUTPUT:
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "muted": false,
    "volume": 100
  }
}

```
</br></br>

---
### List Addons

To retrieve the list of the first five Addons
```
SYNTAX:
  kodi-cli -H kodi001 Addons.GetAddons properties=[name,version,summary] limits={start:0,end:5} -f

OUTPUT:
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "addons": [
      {
        "addonid": "audioencoder.kodi.builtin.aac",
        "name": "AAC encoder",
        "summary": "AAC Audio Encoder",
        "type": "kodi.audioencoder",
        "version": "1.0.2"
      },

      ...
      
      {
        "addonid": "webinterface.default",
        "name": "Kodi web interface - Chorus2",
        "summary": "Default web interface",
        "type": "xbmc.webinterface",
        "version": "19.x-2.4.8"
      }
    ],
    "limits": {
      "end": 5,
      "start": 0,
      "total": 34
    }
  }
}      

```
</br></br>

---
### Display a notification on Kodi UI
To display a warning message on Kodi running on kodi001 for 5 seconds
```
SYNTAX:
   kodi-cli -H kodi001 GUI.ShowNotification title="Dinner Time" message="Time to eat!" image="warning" displaytime=5000

OUTPUT:
{"id":1,"jsonrpc":"2.0","result":"OK"}

```
</br></br>

---
Still TODO:
- Edit parameters prior to call to avoid runtime error.
- Provide additional help/runtime detail on parameters
- Different output formats (rather than just raw and formatted json)

---
### Stream a URL

```
SYNTAX:
    kodi-cli Player.Open item='{file:https://getsamplefiles.com/download/mkv/sample-1.mkv}'

OUTPUT:
{"id":1,"jsonrpc":"2.0","result":"OK"}
```