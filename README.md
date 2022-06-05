# kodi-cli

## Command Line Interface for Kodi

This tool can be used from the command line to execute commands against a target Kodi host via the RPC interface defined at  https://kodi.wiki/view/JSON-RPC_API/v12.  

The available commands are defined via a json file (**kodi_namespaces.json**) which describes all the namespaces, methods and parameters available for managing the kodi device remotely.  

**Note** 
- Not all the commands are fully defined, further iterations of the code will include updates to this file to make more commands available.
- Namespace and Methods are case-sensitive.  Use help or refer to the [Kodi RPC page](https://kodi.wiki/view/JSON-RPC_API/v12) for proper capitalization.
</br></br>

## Some terms:

| Term | Description |
| ------------- | ---------------------------- |
| namespace | The data model is split into namespace components which can be called via the API |
| methods | Each namespace has a number of methods which perform some function within that namespace |
| command | A command is a namespace method combiniation used to control Kodi function (fmt: Namespace.Method) |

```
usage: kodi_cli.py [-h] [-H HOST] [-P PORT] [-u USER] [-p PASSWORD] [-c CONFIG] [-C] [-f] [-v] [command [param ...]]
```
</br></br>

## Overall Description

*Commands* are based on Kodi **namespaces and methods**.  Each namespace (i.e. Application, System,...) has a set of pre-defned methods.  When executing a command you supply the **Namespace.Method parameter(s)** (case-sensitive).

To get a list of parameters (required and optional) for any method, use the command `help` *Namespace.Method*

For example, to display the mute and volume level settings on host kodi001, the command is constructed as follows:
- namespace is *Application*
- method is *GetProperties*
- parameters are *properties=[muted,volume]*

as follows:

  `python kodi_cli.py -H kodi001 Application.GetProperties properties=[muted,volume]`
</br></br>

**TIPS - When calling the script:**
| action | description |
| --------- | ------------------------------ |
| add -h | to display script syntax and list of option parameters |
| enter HELP | as the command for a list of available commands (namespaces) |
| add -C | to create a config file for paraneter defaults |

**To create a configfile:**
  - Compose the command line with all the values desired as defaults
  - Append a -C to command line, the file will be created (if it does not already exist)
  - Any future runs will use the defaults, which can be overridden if needed.
</br>

**Help commands:**
| action | description |
| --------- | ------------------------------ |
| list of namespaces |    `python kodi_cli.py Help` |
| Methods for Namespace | `python kodi_cli.py Help Application` |
| Parameters for Method | `python kodi_cli.py Help Application.GetProperties` |

Details for namespaces, methods and parameters may be found at https://kodi.wiki/view/JSON-RPC_API/v12

The output of the tool is the json response from the Kodi endpoint the command was targeted to. 
(<em>Tip: use the -f parameter to format the json output</em>)
</br></br>

## Prerequsites:

Python packages -
<ul>
<li>requests package</li>
</ul>
</br></br>

---

## Usage

Simply running ***python kodi_cli.py*** will display intro help information.
See below for examples of Kodi commands (i.e. Namespace.Method)

```
usage: kodi_cli.py [-h] -H HOST [-P PORT] [-u USER] [-p PASSWORD] [-v] [command [parameters ...]]

positional arguments:
  command               RPC command in format: Namespace.Method [[Param][Param]]  (help namespace to list)

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Kodi hostname
  -P PORT, --port PORT  Kodi RPC listen port
  -u USER, --user USER  Kodi authenticaetion username
  -p PASSWORD, --password PASSWORD
                        Kodi autentication password
  -c CONFIG, --config CONFIG
                        Optional config file
  -C, --create_config   Create empty config
  -f, --format_output   Format json output
  -v, --verbose         Turn out verbose output, more parms increase verbosity
  ```

---
</br>

## Examples

You can get help from the command line to view namespaces, namespace methods and calling requirements.  Simply
type ***python kodi_cli.py help*** as the command to get a list of all the namespaces.
</br></br>

### Create a config file to store defaults
To minimize command-line entry, you can store defaults in a config file which will be used when running.  The
values can be over-ridded at run-time by provideing the optional argument.

To create a default config file, type your standard defaults as if you were going to execute the CLI and add -C at the end.
The config file will be written with the values.
```
SYNTAX:
  python kodi_cli.py -u myId -p myPassword -P 8080 -C

OUTPUT:
  a file (kodi_cli.cfg will be written as:
    {
      "host": "localhost",
      "port": 8080,
      "user": "myId",
      "password": "myPassword",
      "format_output": false
    }
```
</br></br>

### List all **namespaces**

Namespaces are modules in Kodi, each namespace manages differ aspects of the Kodi interface

```
SYNTAX:
  python kodi_cli.py help

OUTPUT:

  Kodi namespaces -
    Namespace       Methods
    --------------- ----------------------------------------------------------------------------
    AddOns          ExecuteAddon, GetAddonDetails, GetAddons, SetAddonEnabled

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

### List all ***Application*** namespace ***methods***

Each namespace has a number of methods that can be called.  

```
SYNTAX:
  python kodi_cli.py help Application
  or
  python kodi_cli.py Application

OUTPUT:

  Application namespace commands:

  Method                    Description
  ------------------------- --------------------------------------------
  Application.GetProperties Retrieves the values of the given properties
  Application.Quit          Quit application
  Application.SetMute       Toggle mute/unmute
  Application.SetVolume     Set the current volume
```
</br></br>

### List the ***method calling signature*** for a particular namespace method

List the sytax for the Application.SetMute command

```
SYNTAX:
  python kodi_cli.py help Application.SetMute

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
</br></br>

### Example executing a command

To toggle the mute on, then off

```
SYNTAX:
  python kodi_cli.py Application.SetMute mute=toggle

OUTPUT:
  python kodi_cli.py -H MyKodiServer Application.SetMute mute=toggle
  {"id":1,"jsonrpc":"2.0","result":true}

  python kodi_cli.py -H MyKodiServer Application.SetMute mute=toggle
  {"id":1,"jsonrpc":"2.0","result":false}
```
</br></br>

  Still TODO:
  <ul>
  <li>Build out kodi_namespaces.json with additional definitions.</li>
  </ul>