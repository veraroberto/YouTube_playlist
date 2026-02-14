import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from API_KEY import api_key
import requests
import json

from app_functions import create_bookmarks
from filesManager import filesManager
from collections import defaultdict
from paths import (tokens_folder,
                   playlist_folder)


from response import response_manager

default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published 
quota_limit = 9900 # I set at this value since sometime the API doesn't allow for more request when you are to close to the limit.
yt_url = 'https://www.youtube.com/watch?v='
yt_playlist = 'https://www.youtube.com/playlist?list='
yt_channel = 'https://www.youtube.com/channel/'

class YouTubeManager:

    def __init__(self):
        # 1. Store the paths
        self.files_manager = filesManager()
 
        # 2. Authenticate and store the 'youtube' client as 'self.youtube'
        self.youtube = self._authenticate()
        
    def _authenticate(self) -> None:
        SCOPES = ["https://www.googleapis.com/auth/youtube"]
        token_file = tokens_folder / "token.pickle"
        credentials_json = tokens_folder / "credentials.json"

        creds = None

        # Load existing token
        if token_file.exists():
            with open(token_file, "rb") as f:
                creds = pickle.load(f)

        # If no valid credentials, fix them
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_json), SCOPES)
            creds = flow.run_local_server(port=0)

        elif creds.expired and creds.refresh_token:
            creds.refresh(Request())

        # Save back to disk
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

        return build("youtube", "v3", credentials=creds)

    def get_response_video_id(self, video_id: str) -> dict:
        # Now use self.youtube (no need to pass it from notebook)
        response = self.youtube.videos().list(
            part="snippet,contentDetails,liveStreamingDetails",
            id=video_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        return response

    def get_channel_response(self, channel_id: str) -> dict:
        """Fetch the uploads playlist ID for a channel."""
        response = self.youtube.channels().list(
            part="contentDetails,snippet,statistics",
            id=channel_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        return response 

    def get_all_playlists(self) -> list:
        """Retrieve all playlists from the authenticated account."""
        playlists = []
        try:
            # Initialize the request
            request = self.youtube.playlists().list(
                part="snippet,contentDetails,status,player",
                mine=True,  # Fetch playlists from the authenticated account
                maxResults=50  # Maximum number of results per page
            )
            while request:
                response = request.execute()
                self.files_manager.add_to_today_quota(1)
                # Collect playlist names and IDs
                for item in response.get("items", []):
                    playlists.append({
                        "id": item["id"],
                        "name": item["snippet"]["title"]
                    })
                # Get the next page of results if available
                request = self.youtube.playlists().list_next(request, response)
            print("Retrieved all playlists successfully!")
            return playlists #The list is sorted by publishedAt. Desc
        except HttpError as e:
            print(f"An error occurred while getting all the Playlist: {e}")

    def get_subscriptions(self) ->list:
        subscriptions = []
        request = self.youtube.subscriptions().list(
            part="snippet,contentDetails,subscriberSnippet",
            mine=True,
            maxResults=50)
    
        while request:
            response = request.execute()
            self.files_manager.add_to_today_quota(1)
            items = response.get('items', [])
            subscriptions.extend(items)
            request = self.youtube.subscriptions().list_next(request, response)
        return subscriptions

    def get_all_ids_playlist(self, playlist_id: str, max_iterations: int = 5,
                             print_iterations: bool= False) -> list:
        # The API only allows a max_iteration = 400
        """Retrieve all video IDs from a playlist, handling pagination."""
        iterations = 0
        video_ids = []
        try:
            next_page_token = None
            while True:
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,  # Maximum number of items per request
                    pageToken=next_page_token  # Handle pagination
                )
                response = request.execute()
                self.files_manager.add_to_today_quota(1)
    
                # Extract video IDs from the response
                for item in response.get("items", []):
                    video_ids.append(item["snippet"]["resourceId"]["videoId"])
    
                # Check if there's another page of results
                next_page_token = response.get("nextPageToken")
                iterations += 1
                if iterations == max_iterations:
                    break
        
                if not next_page_token:
                    break  # Exit loop when there are no more pages
            if print_iterations:
                print(f'There were {iterations} iterations in the process. The original number of iteration were {max_iterations}')
            return video_ids
        except HttpError as e:
            print(f"An error occurred while getting all the Playlist {playlist_id}: {e}")
            return []
    
    def create_private_playlist(self, title: str, description: str) -> dict | None:
        """Create a private playlist on YouTube."""
        try:
            request = self.youtube.playlists().insert(
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
            self.files_manager.add_to_today_quota(50)
            print(f'Playlist "{title}" was created successfully!')
            print(f"Playlist ID: {response['id']}")
            print('--'*40)
            return response
        except HttpError as e:
            print(f"An error occurred while creating the playlist {title}: {e}")
            return None

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> dict | None:
        """Add a video to a playlist."""
        try:
            request = self.youtube.playlistItems().insert(
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
            self.files_manager.add_to_today_quota(50)
            return response
        except HttpError as e:
            print(f"An error occurred while adding {video_id} in the Playlist {playlist_id}: {e}")
            return None
        
    def delete_video_id_from_playlist(self, playlist_id: str,
                                       video_id_to_delete: str,
                                       print_message: bool = True) -> None:
        # --- Step 1: Find the playlistItemId that matches the videoId ---
        page_token = None
        playlist_item_id = None

        while True:
            response = self.youtube.playlistItems().list(
                part="id,snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token
            ).execute()
            self.files_manager.add_to_today_quota(1)
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
            self.youtube.playlistItems().delete(id=playlist_item_id).execute()
            self.files_manager.add_to_today_quota(50)
            if print_message:
                print(f"\t✅ Video deleted from playlist. Video ID: {video_id_to_delete}")
            return response
        else:
            print("⚠️ Video not found in playlist.")
            return None
   
    def get_response_channel_by_handle(self, handle: str) -> dict:
        handle = "@" + handle.replace('@', "")
        url = f"https://youtube.googleapis.com/youtube/v3/channels?forHandle={handle}&part=snippet,statistics,contentDetails&key={api_key}"
        response = requests.get(url)
        self.files_manager.add_to_today_quota(1)
        data = response.json()
        return data
        # items = data.get('items', {})
        # if not items:
        #     print('There is no')
        # channelId = data['items'][0]['id']
        # channelTitle = data['items'][0]['snippet']['title']
        # uploads = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        # return channelId, channelTitle, uploads

    def get_response_from_playlist_id(self, playlist_id: str) -> dict:
        response = self.youtube.playlists().list(
            part="snippet,contentDetails,id",
            id=playlist_id).execute()

        self.files_manager.add_to_today_quota(1)
        return response

if __name__ =='__main__':
    yt = YouTubeManager()
    fm = filesManager()
    resp_mng = response_manager()
    df = fm.YT_content_creators


    # video_id = '7hTzFn83h4g'
    # res = yt.get_response_video_id(video_id)
    # video_info = resp_mng.get_video_info(res)
    # channelId = video_info['channelId']
    # print(channelId)
    # print(channelId in df['channelId'].values)
    # handle = df[df['channelId'] == channelId]['Handle'].iloc[0]
    # print(handle)

    playlist_names = yt.get_all_playlists()

    youtube_names = [file.stem.replace('_', ' ').strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
    align = max(len(p) for p in youtube_names)
    num_videos = 0
    playlist_dict = defaultdict(list)
    for playlist in youtube_names:
        playlist_id = next((d["id"] for d in playlist_names if playlist in d.values()), None)
        
        if playlist_id:
            video_ids = yt.get_all_ids_playlist(playlist_id, 20, False)
            # print(f'{playlist:<{align}} {len(video_ids):03d} {playlist_id}')
            for video_id in video_ids:
                res = yt.get_response_video_id(video_id)
                video_info = resp_mng.get_video_info(res)
                if not video_info:
                    print(video_id)
                    continue
                channelId = video_info['channelId']
                if channelId in df['channelId'].values:
                    handle = df[df['channelId'] == channelId]['Handle'].iloc[0]
                else:
                    handle = 'Not in DataFrame'
                playlist_dict[handle].append(video_id)
            num_videos += len(video_ids)
    print(f'There are {num_videos} videos in all the playlist')
    
    file_path = f'count_handles.json'
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(playlist_dict, f, ensure_ascii=False, indent=4)



    # subs = yt.get_subscriptions()   
    # missing_sub = {}
    # for s in subs:
    #     snippet = s['snippet']
    #     resourceId = snippet['resourceId']
    #     channelId = resourceId['channelId']
    #     title = snippet['title']
    #     if channelId not in channelId_df:
    #         missing_sub[channelId] = title
    # align = max(len(t) for t in missing_sub.values())
    # for m in missing_sub:
    #     print(f'{missing_sub[m]:<{align}} {yt_channel}{m}')
    # create_bookmarks(missing_sub, f'missing_sub.html', yt_channel)





