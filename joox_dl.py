import argparse
import sys
import os
import requests
from tqdm import tqdm
import eyed3
import json

## pyinstaller --onefile --icon=logo.ico .\joox_dl.py ##

highQuality = None

# download funtion 
def downloadUrl(url, output_path):
    # url = "http://www.ovh.net/files/10Mb.dat" #big file test
    # Streaming, so we can iterate over the response.
    r = requests.get(url, stream=True)
    # Total size in bytes.
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    t=tqdm(total=total_size, unit='iB', unit_scale=True, desc=f'Downloading - {output_path}')
    with open(output_path, 'wb') as f:
        for data in r.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()
    if total_size != 0 and t.n != total_size:
        return False
    return True

# clean value from restricted symbol create folder name etc.
def cleanText(textRaw):
    textClean = textRaw.replace('?', '');
    textClean = textClean.replace('\'', '');
    textClean = textClean.replace('\"', '');
    textClean = textClean.replace(':', '');

    return textClean

def getTrack(songId, albumName = None):
    urlTrack = "http://api.joox.com/web-fcgi-bin/web_get_songinfo?songid=" + songId
    # urlTrack = "http://api.joox.com/web-fcgi-bin/web_get_songinfo?songid=TtEH_iaoAGl1dh5KsV44pg=="

    r = requests.get(urlTrack)
    dataTrackRaw = r.text
    dataTrackRaw = dataTrackRaw[18:-1]
    dataTrack = json.loads(dataTrackRaw)
    dataTrack['msong'] = cleanText(dataTrack['msong'])

    if highQuality:
        link_track = dataTrack['r320Url']
    else:
        link_track = dataTrack['mp3Url']
    
    fileType = link_track.split('?')
    fileType = fileType[0].split('.')
    fileType = fileType[-1]

    fileName = dataTrack['msong'] + '.' + fileType

    if albumName:
        folderPath = 'music/'+ albumName
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
        fullPath = 'music/'+ albumName + '/' + fileName
    else:
        folderPath = 'music'
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
        fullPath = 'music/'+ fileName

    if(downloadUrl(link_track, fullPath)):
        audiofile = eyed3.load(fullPath)

        if (audiofile.tag == None):
            audiofile.initTag()

        audiofile.tag.artist = dataTrack['msinger']
        audiofile.tag.album = dataTrack['malbum']
        audiofile.tag.album_artist = dataTrack['msinger']
        audiofile.tag.title = dataTrack['msong']
        audiofile.tag.comments.set('generated by fajar-isnandio.com')

        if (dataTrack['imgSrc'] != ""):
            responseImg = requests.get(dataTrack['imgSrc'])
            mime_type = contentType = responseImg.headers['content-type']
            img = responseImg.content
            audiofile.tag.images.set(3, img, mime_type)

        audiofile.tag.save()

    return dataTrack

def main():
    parser = argparse.ArgumentParser();
    parser.add_argument('-p', '--playlist', help='Playlist ID ex. (db1J7YbWZ1LectFJqPzd5g==)')
    parser.add_argument('-a', '--album', help='Album ID ex. (fnIkeDK++hFXaAzg7s9Etg==)')
    parser.add_argument('-s', '--song', help='Song ID ex. (TtEH_iaoAGl1dh5KsV44pg==)')
    parser.add_argument('-hq', '--highquality', help='High quality', action='store_true')
    args = parser.parse_args()
    playlistEncode = vars(args)['playlist']
    albumEncode = vars(args)['album']
    songEncode = vars(args)['song']
    global highQuality
    highQuality = vars(args)['highquality']


    if playlistEncode:
        uri = "https://api-jooxtt.sanook.com/openjoox/v1/playlist/" + playlistEncode + "/tracks?country=id&lang=id&index=0&num=50"
    elif albumEncode :
        uri = "https://api-jooxtt.sanook.com/openjoox/v1/album/" + albumEncode + "/tracks?country=id&lang=id&index=0&num=50"        
    elif songEncode :
        uri = "single"
    else:
        uri = None

    if uri == None:
        parser.print_help()
        parser.exit()

    else:
        if songEncode: 
            # downloading track
            song = getTrack(songEncode)
            print(song['msong'] + ' - Selesai!') 
        else:
            # fecthing track
            r = requests.get(uri)
            data = r.json()

            for item in data['tracks']['items']:
                # downloading track
                albumName = cleanText(data['name'])
                getTrack(item['id'], albumName)

                # break
            print(data['name'] + ' : ' + str(data['tracks']['total_count']) + ' lagu.' + ' - Selesai!')
        
if __name__ == '__main__': 
    try:
        main() 
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except requests.ConnectionError as e:
        print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
        print(str(e))
    except requests.Timeout as e:
        print("OOPS!! Timeout Error")
        print(str(e))
    except requests.RequestException as e:
        print("OOPS!! General Error")
        print(str(e))