from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
import youtube_dl
import eyed3
import json
import urllib
import spotipy
import sys
import shutil
from config import CLIENT_SECRET, CLIENT_ID

ydl = youtube_dl.YoutubeDL()

CLIENT_SECRET = CLIENT_SECRET
CLIENT_ID = CLIENT_ID

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

        except:

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

            except:
                print(file, 'FAILED')
                open('log.txt', 'a').write(file)

