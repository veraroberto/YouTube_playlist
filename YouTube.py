import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from API_KEY import api_key
import requests

from filesManager import filesManager



class YouTubeManager:
    yt_url = 'https://www.youtube.com/watch?v='
    def __init__(self):
        # 1. Store the paths
        self.files_manager = filesManager()
        self.tokens_folder = self.files_manager.tokens_folder
        

        # 2. Authenticate and store the 'youtube' client as 'self.youtube'
        self.youtube = self._authenticate()
        
           
    default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published 
    quota_limit = 9900 # I set at this value since sometime the API doesn't allow for more request when you are to close to the limit.
    
    """ 
    def _authenticate(self):
        #Internal method to handle authentication logic
        SCOPES = ["https://www.googleapis.com/auth/youtube"]
        creds = None
        token_file = self.tokens_folder / "token.pickle"
        credentials_json = self.tokens_folder / 'credentials.json'

        if token_file.is_file():
            with open(str(token_file), "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_json), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(str(token_file), "wb") as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)
    """
    def _authenticate(self):
        SCOPES = ["https://www.googleapis.com/auth/youtube"]
        token_file = self.tokens_folder / "token.pickle"
        credentials_json = self.tokens_folder / "credentials.json"

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

    def get_response_video_id(self, video_id):
        # Now use self.youtube (no need to pass it from notebook)
        response = self.youtube.videos().list(
            part="snippet,contentDetails,liveStreamingDetails",
            id=video_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        return response

    def get_channel_response(self, channel_id):
        """Fetch the uploads playlist ID for a channel."""
        response = self.youtube.channels().list(
            part="contentDetails,snippet,statistics",
            id=channel_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        return response 

    def get_all_playlists(self):
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

    def get_subscriptions(self):
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

    def get_all_ids_playlist(self, playlist_id, max_iterations = 5):
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
            return video_ids
        except HttpError as e:
            print(f"An error occurred while getting all the Playlist {playlist_id}: {e}")
            return []
    
    def create_private_playlist(self, title, description):
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

    def add_video_to_playlist(self, playlist_id, video_id):
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
        
    def get_response_channel_by_handle(self, handle):
        handle = "@" + handle.replace('@', "")
        url = f"https://youtube.googleapis.com/youtube/v3/channels?forHandle={handle}&part=snippet,statistics,contentDetails&key={api_key}"
        response = requests.get(url)
        self.files_manager.add_to_today_quota(1)
        data = response.json()
        channelId = data['items'][0]['id']
        channelTitle = data['items'][0]['snippet']['title']
        uploads = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return channelId, channelTitle, uploads


if __name__ =='__main__':
    # ,Andres Agulla,UC7LMKjP8uqyRIjJGr44SY4A,UU7LMKjP8uqyRIjJGr44SY4A
    uploadId = "UU7LMKjP8uqyRIjJGr44SY4A"
    fm = filesManager()
    yt = YouTubeManager()
    file_path = fm.content_creator_folder / 'aagulla.txt'
    video_ids = fm.get_elements_from_file(file_path, create_file=False)
    playlist = yt.get_all_playlists()
    print(playlist)
    new_uploads = yt.get_all_ids_playlist(uploadId, 1)

    for video_id in new_uploads:
        if video_id not in video_ids:
            print(video_id)





