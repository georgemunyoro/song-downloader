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

if len(sys.argv) == 2:
    if sys.argv[1] == '--help' or sys.argv[1] == '-h':
        print('Usage : ')
        print('pydown [text file containing list of songs] [folder to save them to]')
        print('\nExample : ')
        print('pydown songs.txt "/path/to/download/folder"\n')

        quit()

elif len(sys.argv) != 3:
    print('Invalid arguments, use pydown --help for more info')

    quit()

ydl = youtube_dl.YoutubeDL()

creds = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=creds)

SAVE_DIR = sys.argv[2]

if SAVE_DIR[len(SAVE_DIR)-1] != '/':
    SAVE_DIR += '/'

with open(sys.argv[1]) as songlistfile:
    for file in songlistfile:

        file = file.replace('  ', ' ')
        file = file.replace('-', '')
        file = file.replace('(', '')
        file = file.replace(')', '')
        file = ''.join(file.split())

        try:
            print('-'*50)
            print(file)

            metadata = spotify.search(file)['tracks']['items'][0]

            title = metadata['name']
            album = metadata['album']['name']
            date  = metadata['album']['release_date']

            artists = [artist['name'] for artist in metadata['artists']]
            artist = ', '.join(artists)

            image_url = metadata['album']['images'][0]['url']

            # search youtube and download mp3 file

            yt_res = YoutubeSearch(artist + ' ' + file, max_results=1).to_json()
            yt_res = json.loads(yt_res)
            yt_id  = yt_res['videos'][0]['id']

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
                print(['http://www.youtube.com'+yt_res['videos'][0]['link']])
                ydl.download(['http://www.youtube.com'+yt_res['videos'][0]['link']])

            # embed metadata
    #        urllib.request.urlretrieve(image_url, 'cover.jpg')

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

            try:

                yt_res = YoutubeSearch(file).to_json()
                yt_res = json.loads(yt_res)
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
                print(file, 'FAILED')
                open('log.txt', 'a').write(file)

