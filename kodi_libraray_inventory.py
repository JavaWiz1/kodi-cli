import argparse
import json
import pathlib
import textwrap
from typing import Any, List, Tuple

from loguru import logger as LOGGER

import cfg
import kodi_common as util
from kodi_interface import KodiObj

EPISODE_FILE='./episodes.csv'
MOVIE_FILE='./movies.csv'

class KodiCommand:
    TVSHOW_OPTIONS = ['watchedepisodes','season','episode']
    TVSHOW_EPISODE_OPTIONS = ['dateadded','episode','firstaired','playcount','plot','runtime','season','showtitle','title','rating','votes']
    MOVIE_OPTIONS = ['dateadded','genre','lastplayed','mpaa','playcount','plot','plotoutline','premiered','rating','runtime','title','userrating','votes','year']

    def __init__(self, namespace: str, method: str, parms: dict = None) -> None:
        self.namespace = namespace
        self.method = method
        self.parms = parms
        
def _call_kodi(kodi: KodiObj, cmd: KodiCommand) -> bool:
    success = False
    if kodi.check_command(cmd.namespace, cmd.method, cmd.parms):
        kodi.send_request(cmd.namespace, cmd.method, cmd.parms)
        success = kodi.request_success
    return success

def get_tv_shows(kodi: KodiObj) -> List[dict]:
    LOGGER.info(f'Retrieve TVShows from {kodi._host}')
    tv_shows = []
    cmd = KodiCommand('VideoLibrary', 'GetTVShows', {'properties': KodiCommand.TVSHOW_OPTIONS})
    if not _call_kodi(kodi, cmd):
        LOGGER.error(f'ERROR: {kodi.response_status_code} - {kodi.response_text}')
    else:
        r_json = json.loads(kodi.response_text)
        for show in r_json['result']['tvshows']:
            # if show['episode'] > 0 and show['episode'] > show['watchedepisodes']:
            if show['episode'] > 0:
                tv_shows.append(show)
                # print(show)
        LOGGER.info(f'  Total shows:    {r_json["result"]["limits"]["total"]}')
        LOGGER.info(f'  Returned shows: {len(tv_shows)}')

    return tv_shows

def get_tv_show_episodes(kodi: KodiObj, show_name: str, tvshow_id: int, season: int) -> List[dict]:
    episodes = list()
    LOGGER.info(f'- Retrieving {show_name}  season {season}...')
    cmd = KodiCommand('VideoLibrary', 'GetEpisodes', {'tvshowid': tvshow_id, 'season': season, 'properties': KodiCommand.TVSHOW_EPISODE_OPTIONS})
    if not _call_kodi(kodi, cmd):
        LOGGER.error(f'  ERROR: {kodi.response_status_code} - {kodi.response_text}')
    else:
        r_json = json.loads(kodi.response_text)
        for episode in r_json['result']['episodes']:
            entry:dict = {"show_name": show_name}
            entry.update(episode)
            episodes.append(entry)
            # print(episode)
        LOGGER.trace(f'  {len(episodes)} loaded.')
    return episodes

def get_movies(kodi: KodiObj) -> list:
    LOGGER.info('Retrieve Movies...')
    movies = []
    cmd = KodiCommand('VideoLibrary', 'GetMovies', {'properties': KodiCommand.MOVIE_OPTIONS})
    if not _call_kodi(kodi, cmd):
        LOGGER.error(f'ERROR: {kodi.response_status_code} - {kodi.response_text}')
    else:
        r_json = json.loads(kodi.response_text)
        for movie in r_json['result']['movies']:
            movies.append(movie)
        LOGGER.info(f'  Returned movies: {len(movies)}')

    return movies

def create_csv(file_nm: str, entries: list) -> bool:
    header_list = [x for x in entries[0].keys()]
    header_line = ','.join(header_list)
    with pathlib.Path(file_nm).open('w', encoding='UTF-8') as csv_out:
        csv_out.write(f'{header_line}\n')
        for entry in entries:
            detail_list = list()
            for v in entry.values():
                if util.is_integer(v):
                    detail_list.append(str(v))
                elif isinstance(v, dict):
                    v = ','.join(v.values())
                    detail_list.append(f'"{v}"')
                elif isinstance(v, list):
                    v = ','.join(v)
                    detail_list.append(f'"{v}"')
                else:
                    v = v.replace('"', "'")
                    detail_list.append(f'"{v}"')
            detail_line = ",".join(detail_list)
            csv_out.write(f'{detail_line}\n')

def initialize_loggers():
    log_filename = pathlib.Path(cfg.logging_filename) # pathlib.Path('./logs/da-photo.log')

    if cfg.logging_level.upper() == 'INFO':
        console_format = cfg.DEFAULT_CONSOLE_LOGFMT
    else:
        console_format = cfg.DEBUG_CONSOLE_LOGFMT

    c_handle = cfg.configure_logger(log_format=console_format, log_level=cfg.logging_level)
    f_handle = -1
    if cfg.logging_enabled:
        f_handle = cfg.configure_logger(log_filename, log_format=cfg.DEFAULT_FILE_LOGFMT, log_level=cfg.logging_level,
                                       rotation=cfg.logging_rotation, retention=cfg.logging_retention)
        
    # Hack for future ability to dynamically change logging levels
    LOGGER.c_handle = c_handle
    LOGGER.f_handle = f_handle

    if len(cfg.logger_blacklist.strip()) > 0: 
        for logger_name in cfg.logger_blacklist.split(','):
            LOGGER.disable(logger_name)

def apply_overrides(args: argparse.Namespace):
    for key, val in args._get_kwargs():
        cfg_val = getattr(cfg, key, None)
        if cfg_val is not None and cfg_val != val:
            LOGGER.trace(f'CmdLine Override: {key}: {val}')
            setattr(cfg, key, val)
    
    if args.verbose:
        if args.verbose == 1:
            cfg.logging_level = 'INFO'
        elif args.verbose == 2:
            cfg.logging_level = 'DEBUG'
        elif args.verbose > 2:
            cfg.logging_level = 'TRACE'


def main():
    parser = argparse.ArgumentParser(description=f'Kodi CLI controller  v{cfg.__version__}')
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.description = textwrap.dedent('''\
        command is formatted as follows:
            Namespace.Method [parameter [parameter] [...]]

        example - Retrieve list of 5 addons:
            kodi-cli -H myHost Addons.GetAddons properties=[name,version,summary] limits={start:0,end:5}
        ''')
    parser.add_argument("-H","--host", type=str, default=cfg.host, help="Kodi hostname")
    parser.add_argument("-P","--port", type=int, default=cfg.port,help="Kodi RPC listen port")
    parser.add_argument("-u","--kodi-user", type=str, default=cfg.kodi_user,help="Kodi authenticaetion username")
    parser.add_argument("-p","--kodi_pw", type=str, default=cfg.kodi_pw,help="Kodi autentication password")
    parser.add_argument('-t',"--tv-shows", action='store_true')
    parser.add_argument('-m',"--movies", action='store_true')
    parser.add_argument("-v","--verbose", action='count', help="Verbose output, -v = INFO, -vv = DEBUG, -vvv TRACE")
    
    args = parser.parse_args()
    apply_overrides(args)
    initialize_loggers()  # Incase loggers got overridden

    kodi = KodiObj(cfg.host)

    # TODO: set options for watched, unwatched, all (default)
    if args.tv_shows:
        LOGGER.info('='*40)
        episodes = list()
        tv_shows = get_tv_shows(kodi)
        for tvshow in tv_shows:
            show_name = tvshow['label']
            for season in range(1,tvshow['season']):
                season_episodes = get_tv_show_episodes(kodi, tvshow['label'], tvshow['tvshowid'], season )
                if len(season_episodes) > 0:
                    episodes.extend(season_episodes)
            
        create_csv(EPISODE_FILE, episodes)
        LOGGER.success(f'{len(episodes)} episodes loaded into {EPISODE_FILE}')

    if args.movies:
        LOGGER.info('='*40)
        movies = get_movies(kodi)
        create_csv(MOVIE_FILE, movies)
        LOGGER.success(f'{len(movies)} movies loaded into {MOVIE_FILE}')

if __name__ == "__main__":
    main()