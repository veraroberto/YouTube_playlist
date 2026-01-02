from YouTube_fnc import *
# from filesManager import *
from API_KEY import *



from API_KEY import *
import pandas as pd
from YouTube_fnc import *
import isodate, pickle, math, pycountry, requests, string, time, os, itertools, pyperclip, re, unicodedata, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo 
from collections import defaultdict
from IPython.display import clear_output
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Folders and file
Tokens_folder = Path("Tokens")
if not Tokens_folder.exists():
    print(f'The folder {Tokens_folder.stem} was created')
    Tokens_folder.mkdir(parents=True, exist_ok=True)

Content_Creator_folder = Path("Content Creators")
if not Content_Creator_folder.exists():
    print(f'The folder {Content_Creator_folder.stem} was created')
    Content_Creator_folder.mkdir(parents=True, exist_ok=True)
    
playlist_folder =  Path("Playlists")
if not playlist_folder.exists():
    print(f'The folder {playlist_folder.stem} was created')
    playlist_folder.mkdir(parents=True, exist_ok=True)

restrictions_folder = Path('Restrictions')
if not restrictions_folder.exists():
    print(f'The folder {restrictions_folder.stem} was created')
    restrictions_folder.mkdir(parents=True, exist_ok=True)

exceptions_folder = Path('Exceptions')
if not exceptions_folder.exists():
    print(f'The folder {exceptions_folder.stem} was created')
    exceptions_folder.mkdir(parents=True, exist_ok=True)


stats_folder = Path('Stats')
if not stats_folder.exists():
    print(f'The folder {stats_folder.stem} was created')
    stats_folder.mkdir(parents=True, exist_ok=True)
quota_filename = stats_folder / 'Quota.csv'

file_path_yt_creators = stats_folder / 'YT_content_creators.csv'
coolumns = ['Handle', 'channelName', 'channelID', 'uploadsID']
if file_path_yt_creators.exists():
    YT_content_creators = pd.read_csv(file_path_yt_creators)
else:
    YT_content_creators = pd.DataFrame(columns=coolumns)
    
youtube = authenticate_youtube(Tokens_folder)