from kodi_interface import KodiObj
import kodi_common as util
from typing import Any,List,Tuple
import json
import pathlib
from loguru import logger as LOGGER


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
    LOGGER.info('Retrieve TVShows...')
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
            episodes.append(episode)
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

def main():
    kodi = KodiObj("LibreElec7")

    # episodes = list()
    # tv_shows = get_tv_shows(kodi)
    # for tvshow in tv_shows:
    #     for season in range(1,tvshow['season']):
    #         season_episodes = get_tv_show_episodes(kodi,tvshow['label'], tvshow['tvshowid'], season )
    #         if len(season_episodes) > 0:
    #             episodes.extend(season_episodes)
            
    # create_csv(EPISODE_FILE, episodes)
    # LOGGER.info(f'{len(episodes)} episodes loaded into {EPISODE_FILE}')

    movies = get_movies(kodi)
    create_csv(MOVIE_FILE, movies)
    LOGGER.info(f'{len(movies)} movies loaded into {MOVIE_FILE}')

if __name__ == "__main__":
    main()