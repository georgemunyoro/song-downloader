from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
from config import CLIENT_SECRET, CLIENT_ID
import youtube_dl
import eyed3
import json
import urllib
import spotipy
import sys
import shutil
import shelve
from pathlib import Path
from typing import List
import os
import datetime


def create_config_if_nonexistent() -> None:
    config_exists = os.path.exists(str(Path.home()) + '/.songdown/.sdconfig')
    if not config_exists:
        os.mkdir(str(Path.home()) + '/.songdown/')


def set_config_option(config_option: str, new_config_option_value: str) -> None:
    create_config_if_nonexistent()
    user_home_directory = str(Path.home())
    with shelve.open(f'{user_home_directory}/.songdown/.sdconfig') as config_db:
        config_db[config_option] = new_config_option_value


def get_config_value(config_option: str) -> str:
    create_config_if_nonexistent()
    user_home_directory = str(Path.home())
    with shelve.open(f'{user_home_directory}/.songdown/.sdconfig') as config_db:
        try:
            return config_db[config_option]
        except KeyError:
            print('CLIENT_ID and CLIENT_SECRET not set, set them before downloading')
            quit()


def spotify_credentials() -> SpotifyClientCredentials:
    client_id = get_config_value('client_id')
    client_secret = get_config_value('client_secret')
    return SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)


def generate_spotify_client() -> spotipy.Spotify:
    ydl = youtube_dl.YoutubeDL()
    return spotipy.Spotify(client_credentials_manager=spotify_credentials())


def get_song_list_from_song_file(song_list_filepath: str) -> List[str]:
    with open(song_list_filepath) as song_list_file:
        return song_list_file.readlines()


def main(spotify: spotipy.Spotify) -> None:
    songs_to_download = get_song_list_from_song_file(sys.argv[1])
    SAVE_DIR = sys.argv[2]

    if SAVE_DIR[-1] != '/':
        SAVE_DIR += '/'

    for song in songs_to_download:
        song = song.replace('  ', ' ')
        song = song.replace('-', '')
        song = song.replace('(', '')
        song = song.replace(')', '')
        song = ' '.join(song.split())

        try:
            print('-'*50)
            print(song)

            metadata = spotify.search(song)['tracks']['items'][0]

            title = metadata['name']
            album = metadata['album']['name']
            date  = metadata['album']['release_date']

            artists = [artist['name'] for artist in metadata['artists']]
            artist = ', '.join(artists)

            image_url = metadata['album']['images'][0]['url']

            # search youtube and download mp3 file
            yt_res = json.loads(YoutubeSearch(artist + ' ' + song, max_results=1).to_json())
            yt_id  = yt_res['videos'][0]['id']

            print(yt_res)

            ydl_opts = {
                'outtmpl': SAVE_DIR + u'%(id)s.%(ext)s',
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                print(['http://www.youtube.com'+yt_res['videos'][0]['url_suffix']])
                ydl.download(['http://www.youtube.com'+yt_res['videos'][0]['url_suffix']])

            # embed metadata
            track_file = eyed3.load(f'{SAVE_DIR}{yt_id}.mp3')
            track_file.tag.artist = str(artist)
            track_file.tag.album  = str(album)
            track_file.tag.album_artist = str(metadata['album']['artists'][0]['name'])
            track_file.tag.title = str(title)
            track_file.tag.track_num = int(metadata['track_number'])

            data = urllib.request.urlopen(image_url).read()

            track_file.tag.images.set(3, data, "image/jpeg", u"")
            track_file.tag.save()

            shutil.move(f'{SAVE_DIR}{yt_id}.mp3', f'{SAVE_DIR}{artist} - {title}.mp3')

            print(title)
            print(album)
            print(date)
            print(artist)
            print(image_url)

            print('-'*50)

        except Exception as e:

            print(e)

            try:

                yt_res = json.loads(YoutubeSearch(song).to_json())
                yt_id  = yt_res['videos'][0]['id']

                ydl_opts = {
                    'outtmpl': SAVE_DIR + u'%(title)s.%(ext)s',
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(['http://www.youtube.com'+yt_res['videos'][0]['link']])

            except Exception as e:
                print(e)
                print(song, 'FAILED')
                open('log.txt', 'a').write(f'\n[{str(datetime.datetime.now())}] {song}')


def parse_arguments() -> None:
    def invalid_arguments():
        print('Invalid arguments, use pydown --help for more info')
        quit()

    if len(sys.argv) == 2:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("""

            Usage:
                python downloader.py <text file containing list of songs> <folder to save files in>
                python downloader.py config [client_id | client_secret] <value>
                python downloader.py install

            """)
            quit()

    elif len(sys.argv) == 4 and sys.argv[1] == 'config':
        set_config_option(sys.argv[2], sys.argv[3])

    elif len(sys.argv) != 3:
        invalid_arguments()

    else:
        print(generate_spotify_client())
        main(generate_spotify_client())


if __name__ == '__main__':
    parse_arguments()

