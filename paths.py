from pathlib import Path
import os

import os
from pathlib import Path

# 1. Project Root Directory (Where the .py code lives)
PROJECT_ROOT = Path(__file__).resolve().parent

# 2. Check if a custom data directory is specified via Environment Variable (e.g., for Google Drive)
CUSTOM_DATA_DIR = os.getenv("YOUTUBE_TRACKER_DATA_DIR")

if CUSTOM_DATA_DIR:
    DATA_DIR = Path(CUSTOM_DATA_DIR)
else:
    # 3. Default path for general end-users: "Documents/YouTubeTracker"
    # Works cross-platform on Windows, macOS, and Linux out of the box
    DATA_DIR = Path.home() / "Documents" / "YouTubeTracker"

# Automatically create the data directory if it doesn't exist yet
DATA_DIR.mkdir(parents=True, exist_ok=True)



content_creator_folder = DATA_DIR / 'Content Creators'
content_creator_folder_response = DATA_DIR / 'Content Creators Response'
exception_folder = DATA_DIR / 'Exceptions'
playlist_folder =  DATA_DIR / "Playlists"
restriction_folder = DATA_DIR / 'Restrictions'
stats_folder = DATA_DIR / 'Stats'
tokens_folder = DATA_DIR / "Tokens"
html_folder = DATA_DIR / 'HTML'

if not content_creator_folder.exists():
    content_creator_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {content_creator_folder.stem} was created')

if not content_creator_folder_response.exists():
    content_creator_folder_response.mkdir(parents=True, exist_ok=True)
    print(f'The folder {content_creator_folder_response.stem} was created')

if not exception_folder.exists():
    exception_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {exception_folder.stem} was created')

if not playlist_folder.exists():
    playlist_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {playlist_folder.stem} was created')

if not restriction_folder.exists():
    restriction_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {restriction_folder.stem} was created')

if not stats_folder.exists():
    stats_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {stats_folder.stem} was created')

if not tokens_folder.exists():
    tokens_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {tokens_folder.stem} was created')

if not html_folder.exists():
    html_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {html_folder.stem} was created')        



clear_row = '\033[K'
columns_df = ['Handle', 'channelTitle', 'channelId', 'uploads']

yt_url = 'https://www.youtube.com/watch?v='
yt_playlist = 'https://www.youtube.com/playlist?list='
yt_channel = 'https://www.youtube.com/channel/'




