# Podcast Downloader

A simple podcast downloading program that will write customizable metadata to ID3 tags embedded in each file.

## Installation

**Requires python 3.6 or newer**

    % git clone https://github.com/mcarlton00/podcast-downloader
    % cd podcast downloader
    % pip install -r requirements.txt

## Usage

1. Set up your config file in the same directory as `podcast-downloader.py` with your desired storage path and the details of the various feeds that you'd like to download

```json
{
    "path": "/media/Podcasts",
    "podcasts": {
        "No Instructions": {
            "feed": "https://www.iliketomakestuff.com/feed/podcast/no-instructions-audio-podcast"
        },
        "The Way I Heard It": {
            "feed": "http://thewayiheardit.rsvmedia.com/rss/",
            "artist": "Mike Rowe", # Optional
            "album": "The Way I Heard It with Mike Rowe" # Optional
        },
    }
}
```

  * Note that `feed` is the only required field.  `artist` and `album` are optional if you'd like to manually define metadata for a given podcast series.  If they're left blank, they will default to using the podcast name for both fields.

2. Run the downloader: `/path/to/python3 podcast-downloader.py`.  It will print progress as it works through each feed in your config file.
