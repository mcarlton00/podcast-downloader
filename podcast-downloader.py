import json
import io
import os
import re
import sys

import mutagen
from mutagen.easyid3 import EasyID3
import podcastparser
import requests
import yaml

def load_config():
    path = os.path.dirname(os.path.abspath(__file__))
    with open(f'{path}/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    return config

def read_cache(path):

    if os.path.isfile(f'{path}/downloaded_episodes.json'):
        with open(f'{path}/downloaded_episodes.json', 'r') as f:
            cache = json.load(f)
    else:
        cache = {}

    return cache

def write_cache(path, cache):
    print('Writing cache file')
    with open(f'{path}/downloaded_episodes.json', 'w') as f:
        json.dump(cache, f)


def download_file(path, filename, episode):
    # Downloads the podcast episode
    # Some sites were blocking the default useragent of requests
    headers = {'User-Agent': "Podcast Downloader Bot"}
    if episode.get('enclosures'):
        url = episode.get('enclosures')[0].get('url')
        try:
            with requests.get(url, headers=headers) as r:
                r.raise_for_status()
                if r.content:
                    with open(f"{path}/{filename}", 'wb') as f:
                        f.write(r.content)
                        f.close()
                        return True
                else:
                    print("Episode contents were empty -- Skipping")
        except:
            print(f'Error downloading {filename} from {url}')
            pass
    else:
        print(f'No download link found for {filename}')
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
    if attribs.get('track_num'):
        tags['tracknumber'] = str(attribs.get('track_num'))
    tags.save()

    return

def find_track_num(title):
    # https://regex101.com/r/riK5vw/3
    reg_match = '(#|[Ee]pisode|[Ee]p)( |_|-|\.|#)*?(\d+)|^(\d+)(?!\.\d+)| (\d+)[ :-_].*$'

    matches = re.search(reg_match, title)

    if matches:
        track_num = [ int(match) for match in matches.groups()
                     if match and match.isdigit() ][0]
    else:
        track_num = 0

    return '{:03d}'.format(track_num)


if __name__ == '__main__':
    config = load_config()
    root_path = config.get('path')
    cache = read_cache(root_path)
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
            title = episode.get('title')
            if not cache.get(podcast):
                cache[podcast] = []
            if title not in cache.get(podcast, []):
                filename = title.replace(' ', '_').replace('/', '-').strip('.')
                url = episode.get('enclosures')[0].get('url')
                extension = url[-4:]
                filename += extension
                if not os.path.isfile(f'{path}/{filename}'):
                    # Download if the file doesn't already exist
                    print(f'Downloading "{filename}"')
                    attribs['track_num'] = find_track_num(title)
                    dl_file = download_file(path, filename, episode)
                    if dl_file:
                        if cache.get(podcast):
                            cache[podcast].append(title)
                        else:
                            cache[podcast] = [ title ]
                        make_tags(podcast, attribs, path, filename, episode)
                    results[podcast].append(episode)
                elif config.get('overwrite_tags', False):
                    # If the file exists but overwrite_tags is set, make new tags
                    attribs['track_num'] = find_track_num(title)
                    make_tags(podcast, attribs, path, filename, episode)
                    results[podcast].append(episode)
                else:
                    print(f"Episode '{filename}' already exists")
                    if cache.get(podcast, None) is not None:
                        if title not in cache[podcast]:
                            cache[podcast].append(title)
    write_cache(root_path, cache)
