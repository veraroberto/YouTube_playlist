from API_KEY import *
import pandas as pd
from filesManager import *
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


response = requests.get('http://ipinfo.io')
data = response.json()
current_country = data.get('country', "")
if not current_country:
    print('No conuntry was found.')

# YouTube URL
yt_url = 'https://www.youtube.com/watch?v='
yt_channel = 'https://www.youtube.com/channel/'
playlist_url = 'https://www.youtube.com/playlist?list='

exceptions_folder = Path('Exceptions')

def authenticate_youtube(Tokens_folder):
    SCOPES = ["https://www.googleapis.com/auth/youtube"]
    """Authenticate the user and return the YouTube API client."""
    creds = None
    token_file = Tokens_folder / "token.pickle"
    credentials_json = Tokens_folder / 'credentials.json'
    # Load credentials if they already exist
    if token_file.is_file():
        with open(token_file, "rb") as token:
            creds = pickle.load(token)
    # If no credentials or they are invalid, perform authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def get_response_video_id(youtube, quota_filename, video_id):
    response = youtube.videos().list(
        part="snippet,contentDetails,liveStreamingDetails",
        id=video_id
    ).execute()
    add_to_today_quota(quota_filename, 1)
    return response

def get_metadata_video(response):
    items = response.get('items',[])
    if not items:
        return []
    
    video_url = yt_url + response['items'][0]['id']
    snippet = items[0].get('snippet', {})
    publishedAt = snippet.get('publishedAt', "")
    title = snippet.get('title', "")
    channelTitle = snippet.get('channelTitle', "")
    contentDetails = items[0].get('contentDetails', {})
    duration_iso = contentDetails.get('duration', 'PT0S')
    duration = isodate.parse_duration(duration_iso).total_seconds()
    metadata_video = [title, channelTitle, video_url, publishedAt, duration_string(duration)]
 
    regionRestriction = contentDetails.get('regionRestriction',{})
    blocked = regionRestriction.get('blocked', [])
    allowed = regionRestriction.get('allowed', [])
    if current_country in blocked:
        metadata_video.append(f'The video is blocked in: {",".join(current_country)}')
    elif allowed and current_country not in allowed:
         metadata_video.append(f'The video is only allowed in {", ".join(allowed)} ')
        
    return metadata_video

def is_short(video_id):
    url = f'https://www.youtube.com/shorts/{video_id}'
    response = requests.get(url, allow_redirects=True)
    if response.status_code == 429:
        print("Too many requests — you've hit a rate limit.")
        return "Error"
    elif response.status_code == 403:
        print("Access forbidden — you may be blocked.")
        return "Error"
    
    # The final URL after redirects
    final_url = response.url

    # If it redirects to the watch URL, it's not a Short
    if 'youtube.com/watch?v=' in final_url:
        return False
    elif 'youtube.com/shorts/' in final_url:
        return 'Is short'
    else:
        return None  # Unexpected case
    
def is_restricted(response):
    items = response['items']
    if items:
        details = items[0]['contentDetails']
        regionRestriction = details.get('regionRestriction',{})
        blocked = regionRestriction.get('blocked', [])
        allowed = regionRestriction.get('allowed', [])
        if current_country in blocked or (allowed and current_country not in allowed):
            return True
    else:
        print('There is no items response')

def get_channel_response(youtube, quota_filename, channel_id):
    """Fetch the uploads playlist ID for a channel."""
    response = youtube.channels().list(
        part="contentDetails,snippet,statistics",
        id=channel_id
    ).execute()
    add_to_today_quota(quota_filename, 1)
    return response 

def get_response_channelby_handle(youtube, quota_filename, handle):
    handle = "@" + handle.replace('@', "")
    url = f"https://youtube.googleapis.com/youtube/v3/channels?forHandle={handle}&part=snippet,statistics,contentDetails&key={api_key}"
    response = requests.get(url)
    add_to_today_quota(quota_filename, 1)
    data = response.json()
    channelId = data['items'][0]['id']
    channelTitle = data['items'][0]['snippet']['title']
    uploads = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return channelId, channelTitle, uploads

def get_response_from_playlist_id(youtube, quota_filename, playlist_id):
    response = youtube.playlists().list(
        part="snippet,contentDetails",
        id=playlist_id).execute()

    add_to_today_quota(quota_filename, 1)
    return response

def create_private_playlist(youtube, quota_filename, title, description):
    """Create a private playlist on YouTube."""
    try:
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["example", "private", "playlist"],
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"  # Options: 'private', 'public', 'unlisted'
                },
            },
        )
        response = request.execute()
        add_to_today_quota(quota_filename, 50)
        print(f'Playlist "{title}" was created successfully!')
        print(f"Playlist ID: {response['id']}")
        print('--'*40)
        return response
    except HttpError as e:
        print(f"An error occurred while creating the playlist {title}: {e}")
        return None

def get_all_playlists(youtube, quota_filename):
    """Retrieve all playlists from the authenticated account."""
    playlists = []
    try:
        # Initialize the request
        request = youtube.playlists().list(
            part="snippet",
            mine=True,  # Fetch playlists from the authenticated account
            maxResults=50  # Maximum number of results per page
        )
        while request:
            response = request.execute()
            add_to_today_quota(quota_filename, 1)
            # Collect playlist names and IDs
            for item in response.get("items", []):
                playlists.append({
                    "id": item["id"],
                    "name": item["snippet"]["title"]
                })
            
            # Get the next page of results if available
            request = youtube.playlists().list_next(request, response)
            
        print("Retrieved all playlists successfully!")
        return playlists
    except HttpError as e:
        print(f"An error occurred while getting all the Playlist: {e}")
        return playlists

def add_video_to_playlist(youtube, quota_filename, playlist_id, video_id):
    """Add a video to a playlist."""
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,  # The ID of the playlist
                    "resourceId": {
                        "kind": "youtube#video",  # Specify the type as a YouTube video
                        "videoId": video_id,  # The ID of the video
                    }
                }
            }
        )
        response = request.execute()
        add_to_today_quota(quota_filename, 50)
        return response
    except HttpError as e:
        print(f"An error occurred while adding {video_id} in the Playlist {playlist_id}: {e}")
        return None

def get_all_ids_playlist(youtube, quota_filename, playlist_id, max_iternations = 5):
    """Retrieve all video IDs from a playlist, handling pagination."""
    iterations = 0
    video_ids = []
    try:
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,  # Maximum number of items per request
                pageToken=next_page_token  # Handle pagination
            )
            response = request.execute()
            add_to_today_quota(quota_filename, 1)

            # Extract video IDs from the response
            for item in response.get("items", []):
                video_ids.append(item["snippet"]["resourceId"]["videoId"])

            # Check if there's another page of results
            next_page_token = response.get("nextPageToken")
            iterations += 1
            if iterations == max_iternations:
                break
    
            if not next_page_token:
                break  # Exit loop when there are no more pages
        return video_ids
    except HttpError as e:
        print(f"An error occurred while getting all the Playlist {playlist_id}: {e}")
        return []
                
def get_subscriptions(quota_filename):
    subscriptions = []
    request = youtube.subscriptions().list(
        part="snippet",
        mine=True,
        maxResults=50
    )

    while request:
        response = request.execute()
        add_to_today_quota(quota_filename, 1)
        for item in response['items']:
            title = item['snippet']['title']
            channel_id = item['snippet']['resourceId']['channelId']
            subscriptions.append((title, channel_id))
        request = youtube.subscriptions().list_next(request, response)
    return subscriptions

def delelte_video_id_from_playlist(youtube, quota_filename, video_id_to_delete, playlist_id, print_message = True):
    items_per_page = 50
    # --- Step 1: Find the playlistItemId that matches the videoId ---
    page_token = None
    playlist_item_id = None

    while True:
        response = youtube.playlistItems().list(
            part="id,snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()
        add_to_today_quota(quota_filename, 1)
        for item in response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            if video_id == video_id_to_delete:
                playlist_item_id = item["id"]
                if print_message:
                    print(f"\t🎯 Video ID {video_id_to_delete} found in the playlist")
                break

        if playlist_item_id or "nextPageToken" not in response:
            break

        page_token = response["nextPageToken"]

    # --- Step 2: Delete the video from the playlist ---
    if playlist_item_id:
        youtube.playlistItems().delete(id=playlist_item_id).execute()
        add_to_today_quota(quota_filename, 50)
        if print_message:
            print(f"\t✅ Video deleted from playlist. Video ID: {video_id_to_delete}")
        return response
    else:
        print("⚠️ Video not found in playlist.")
    

        
def get_podcast_name_videoID(youtube, quota_filename, YT_content_creators, video_id, channelId):
    only_playlist = YT_content_creators[YT_content_creators['uploadsID'].str.startswith('PL')].reset_index(drop=True)
    if channelId not in only_playlist['channelID'].values:
        print(f'{yt_url}{video_id}')
        print('The channelID is not in DataFrame')
        return 
    else:
        filter_df = YT_content_creators[YT_content_creators['channelID'] == channelId].reset_index(drop=True)
        for index, playlistID in enumerate(filter_df['uploadsID'].values, 1):
            playlist_ids = get_all_ids_playlist(youtube, quota_filename, playlistID, max_iternations = 1)
            if video_id in playlist_ids:
                Handle = YT_content_creators[YT_content_creators['uploadsID'] == playlistID]['Handle'].iloc[0]
                return Handle
    print('The channelID is in the DataFrame, but not the Playlist or Podcast')


    
def write_csv_safely(df, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        df.to_csv(f, index=False, date_format="%Y-%b-%d")
 


def add_to_today_quota(filename, new_quota):
    pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
    today_str = pst_time.strftime('%Y-%b-%d')

    if not filename.is_file():
        df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
        df['Quota'] = df['Quota'].astype(int)
        write_csv_safely(df, filename)
        print(f"The file {filename.stem} was created")
        return

    try:
        df = pd.read_csv(filename,  encoding="utf-8")
    except Exception:
        df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
        df['Quota'] = df['Quota'].astype(int)
        write_csv_safely(df, filename)
        return

    if 'Date' not in df.columns or 'Quota' not in df.columns:
        df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
        df['Quota'] = df['Quota'].astype(int)
        write_csv_safely(df, filename)
        return

    # Normalize date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%b-%d')

    if today_str in df['Date'].values:
        df.loc[df['Date'] == today_str, 'Quota'] = (
            df.loc[df['Date'] == today_str, 'Quota'].astype(int) + new_quota
        )
    else:
        df = pd.concat(
            [df, pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])],
            ignore_index=True
        )

    # Ensure 'Quota' column is integer
    df['Quota'] = df['Quota'].astype(int)

    write_csv_safely(df, filename)


    
def get_today_quota(filename, print_statement = False):    
    #today_str = datetime.today().strftime('%Y-%b-%d')
    pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
    today_str = pst_time.strftime('%Y-%b-%d')

    # If file doesn't exist, create it with headers
    if not filename.exists():
        df = pd.DataFrame(columns=['Date', 'Quota'])
        df.to_csv(filename, index=False)
        return 0

    try:
        df = pd.read_csv(filename,  encoding="utf-8")
    except Exception:
        # If the file can't be read for some reason, treat it as empty
        return 0

    if df.empty or 'Date' not in df.columns or 'Quota' not in df.columns:
        return 0

    # Normalize date format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%b-%d')
    
    # Find row with today's date
    quota_row = df[df['Date'] == today_str]
            
    if not quota_row.empty:
        current_quota = quota_row.iloc[0]['Quota']
        if print_statement:
            print(f'The current quota usage is: {int(current_quota):,}')
        return current_quota
    else:
        print(f'The current quota usage is 0')
        return 0

def choose_option(options, message="Enter your choice: "):
    pyperclip.copy('')
    
    # 1. Generate Excel-style labels (a, b... z, aa, ab...)
    def get_labels(count):
        labels = []
        n = 1
        while len(labels) < count:
            # Generate combinations of length n ('a', then 'aa', then 'aaa')
            for combo in itertools.product(string.ascii_uppercase, repeat=n):
                labels.append("".join(combo))
                if len(labels) == count:
                    break
            n += 1
        return labels

    # 2. Map labels to options
    option_labels = get_labels(len(options))
    option_map = dict(zip(option_labels, options))

    while True:
        print(message)
        for letter, option in option_map.items():
            print(f"  {letter}) {option}")
        choice = input("Enter your choice: ").strip().upper()
        # Check for user input or the pyperclip bypass
        if choice in option_map or pyperclip.paste() == 'choose_option':
            if pyperclip.paste() == 'choose_option':
                print('There was no option chosen and the function was interrupted')
                return None
            
            print(f"  {choice}) {option_map[choice]}")
            return option_map[choice]
        else:
            print("Invalid choice. Please try again.\n")

def add_exception_to_file(handle):
    
    add_to_exceptions = choose_option([True, False], 'Add the handle to an Exception File:')
    expection_handles = [handle.stem for handle in exceptions_folder.iterdir() if handle.suffix == '.txt']
    added_exception = defaultdict(list)
    print('--'*40)
    while add_to_exceptions:
        
        exception = choose_option(expection_handles, 'Choose Exception:')
        exception_file = exceptions_folder / f'{exception}.txt'
        if exception == 'skip_title':
            title_to_skip = remove_accents(input('Title to Skip: ').strip().lower())
            add_element_to_file(exception_file, title_to_skip, True, True)
            added_exception[exception].append(title_to_skip)
        else:
            added_exception[exception].append(handle)
            add_element_to_file(exception_file, handle, True, True)   
        print('**'*40)
        add_to_exceptions = choose_option([True, False], 'Another exception? ')
    clear_output(wait=False)
    if added_exception:
        print('The added exception are')
    for exception in added_exception.keys():
        print(f'{exception}: ')
        for exc in added_exception[exception]:
            print('\t' + exc)
        print('++'*40)

def get_index(url):
    url = url.replace('shorts/', 'watch?v=')
    if 'watch?v=' not in url:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return int(query.get("index", [0])[0])  # default to 0 if missing

def get_video_id(url):
    url = url.replace('https://www.youtube.com/shorts/', 'https://www.youtube.com/watch?v=')
    if 'https://www.youtube.com/watch?v=' not in url:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("v", [0])[0]  # default to 0 if missing

def add_restriction_df(restrictions_folder, Handle, response):

    if not restrictions_folder.exists():
        restrictions_folder.mkdir(parents=True, exist_ok=True)
        print(f'Folder {restrictions_folder.name} was created')

    handle_restricted = restrictions_folder / f'{Handle}.csv'

    columns_restricted_df = ['videoID','title', 'publishedAt', 'restriction']
    if not handle_restricted.exists():
        df = pd.DataFrame(columns = columns_restricted_df)
    else:
        df = pd.read_csv(handle_restricted, encoding="utf-8")

    items = response.get('items', [])
    if not items:
        print("Response dosen't have have items")
        return
    videoID = items[0].get('id', "")
    if videoID in df['videoID'].values:
        print('Video ID already in the Restricted Data Frame')
        return
    if not is_restricted(response):
        print(f'The response is not restricted: {yt_url}{videoID} ')
        return videoID
    snippet = items[0].get('snippet', {})
    publishedAt = snippet.get('publishedAt', '')
    title = snippet.get('title', '')
    contentDetails = items[0].get('contentDetails', {})
    regionRestriction = contentDetails.get('regionRestriction', {})
    restriction = ""
    if regionRestriction:
        for res, countries in regionRestriction.items():
            restriction += f'{res}: {", ".join(countries)}.'
    new_row_data = [videoID,title, publishedAt, restriction]
    
    df.loc[len(df)] = new_row_data
    df.sort_values(by="publishedAt", ascending=True, inplace=True, ignore_index=True)
    write_csv_safely(df, handle_restricted)
    
# def load_all_strings_txt_folder(folder: Path) -> set[str]:
def load_all_strings_txt_folder(folder):
    all_strings = set()
    for file in folder.glob("*.txt"):
        with file.open("r", encoding="utf8", errors="ignore") as f:
            for line in f:
                all_strings.add(line.strip())
    return all_strings

def duration_string(duration):
    #Duration in seconds
    if isinstance(duration, (float, int)):
        hrs, mins = divmod(duration, 3600)
        mins, secs = divmod(mins, 60)
        duration_string = f'{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}'
        return duration_string
    else:
        print(f'{duration} is not a number')

def get_elements_from_file(file_path):
    file_path = file_path.with_suffix('.txt')
    file_path.touch()
    elements = file_path.read_text(encoding="utf-8").splitlines()
    return elements

def add_list_to_file(file_path, list_elements, sort_list = True):
    file_path = file_path.with_suffix('.txt')
    elements_file = get_elements_from_file(file_path)
    for e in list_elements:
        if e not in elements_file:
            elements_file.append(e)
    if sort_list:
        elements_file.sort(key= str.lower)

    with file_path.open(mode="w", encoding="utf-8", newline="\n") as f:
        f.write('\n'.join(map(str, elements_file)))
        
    return elements_file

def add_element_to_file(file_path, element, sort_list = True, print_statement = False):
    file_path = file_path.with_suffix('.txt')
    elements = get_elements_from_file(file_path)
    if element not in elements:
        elements.insert(0,element)
    else:
        if print_statement:
            print(f'{element} is already in {file_path.name}')
    if sort_list:
        elements.sort(key= str.lower)
    add_list_to_file(file_path, elements, sort_list)
    return elements

def remove_accents(text: str) -> str:
    # Normalize the text to separate base letters and diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Filter out the diacritic marks
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents