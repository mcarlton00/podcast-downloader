import yaml
import io
import os
import sys

import mutagen
from mutagen.easyid3 import EasyID3
import podcastparser
import requests

def load_config():
    path = os.path.dirname(os.path.abspath(__file__))
    with open(f'{path}/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    return config

def download_file(path, filename, episode):
    # Downloads the podcast episode
    # Some sites were blocking the default useragent of requests
    headers = {'User-Agent': "Podcast Downloader Bot"}
    if episode.get('enclosures'):
        url = episode.get('enclosures')[0].get('url')
        with requests.get(url, headers=headers) as r:
            r.raise_for_status()
            if r.content:
                with open(f"{path}/{filename}", 'wb') as f:
                    f.write(r.content)
                    f.close()
                    return True
            else:
                print("Episode contents were empty -- Skipping")
    else:
        print('No download link found for {filename}')
    return False

def make_tags(podcast, attribs, path, filename, episode):
    # Tag the episode with ID3 metadata
    print(f"-- Tagging {filename}")
    try:
        try:
            tags = EasyID3(f"{path}/{filename}")
        except:
            tags = mutagen.File(f"{path}/{filename}", easy=True)
    except:
        print(f"############ Unable to open {path}/{filename} for tagging ############")
        sys.exit()

    tags['title'] = episode.get('title', filename)
    tags['artist'] = attribs.get('artist', podcast)
    tags['album'] = attribs.get('album', podcast)
    genres = attribs.get('genres', [])
    genres.append('Podcast')
    tags['genre'] = ','.join(genres)
    tags.save()

    return

if __name__ == '__main__':
    config = load_config()
    root_path = config.get('path')
    results = {}
    # Some feeds block the default requests user agent
    headers = {'User-Agent': "Podcast Downloader Bot"}
    for podcast,attribs in config.get('podcasts').items():
        print(f"==== Processing '{podcast}' ====")
        feed = requests.get(attribs.get('feed'), headers=headers)
        feed_bytes = io.BytesIO(feed.content)
        parsed_feed = podcastparser.parse(attribs.get('feed'), feed_bytes)
        path = f"{root_path}/{podcast.replace(' ', '_')}"
        results[podcast] = []

        try:
            os.makedirs(path)
        except:
            pass

        for episode in parsed_feed.get('episodes'):
            filename = f"{episode.get('title').replace(' ', '_').encode('ascii', 'ignore').decode().strip('.')}.mp3".replace('/', '-')
            if not os.path.isfile(f"{path}/{filename}"):
                print(f"Downloading '{filename}'")
                dl_file = download_file(path, filename, episode)
                if dl_file:
                    make_tags(podcast, attribs, path, filename, episode)
                results[podcast].append(episode)
            else:
                print(f"Episode '{filename}' already exists")
