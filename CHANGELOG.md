# 0.2.1 02/15/2024
- Switched to loguru for logging
- changed how config works, default location is ~/.kodi_cli/kodi_cli.cfg
- location of the log file will be in same directory as config (~/.kodi_cli)

# 0.1.9 10/24/2023
- Fix bug for locating json definition files
- Fix bug for handling boolean input parameters

# 0.1.8 10/23/2023
- README.md documentation updates
- logging updates -v INFO -vv TRACE (new) -vvv DEBUG

# 0.1.7 10/23/2022
- Use official kodi repo json files for methods and type definitions (replacing kodi_namespaces.json)
- Updated parsing for help messages
- bug fix for building paraneter strings when calling the RPC endpoints 

# 0.1.6 8/13/2022
- Fixed AddOn.GetAddons 
- Set following as defaults in GetAddons: property=[name] limit={start=0,max=99}
- Handle objects in parameters (treat as dictionary)

# 0.1.3 6/29/2022
- Fix distribution
- Add kodi_help_tester.py - used to check the help output

# 0.1.2 6/19/2022
- repackage code, split KodiObj into own module
- clean up distribution 
- README updates
