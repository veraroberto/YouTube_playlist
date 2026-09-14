import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from API_KEY import (api_key,
                     watch_later_id)
import requests

from collections import Counter
from pathlib import Path
from functools import partial

from app_functions import (create_bookmarks,
                           duration_string,
                           choose_option,
                           get_playlist_id,
                           get_video_id,
                           clear_terminal,
                           print_dictionary
                           )

from filesManager import filesManager
from collections import defaultdict
from paths import (tokens_folder)

from typing import cast
from urllib.parse import (urlparse,
                          parse_qs)
from response import response_manager
from paths import (yt_url,
                   yt_playlist,
                   yt_channel)

default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published 
quota_limit = 9900 # I set at this value since sometime the API doesn't allow for more request when you are to close to the limit.

class YouTubeManager:

    def __init__(self):
        # 1. Store the paths
        self.files_manager = filesManager()
        self.response_mng = response_manager()
 
        # 2. Authenticate and store the 'youtube' client as 'self.youtube'
        self.youtube = self._authenticate()
        
    def _authenticate(self):
        SCOPES = ["https://www.googleapis.com/auth/youtube"]
        token_file = tokens_folder / "token.pickle"
        credentials_json = tokens_folder / "credentials.json"

        credentials = None

        # Load existing token
        if token_file.exists():
            with open(token_file, "rb") as f:
                credentials = pickle.load(f)

        # If no valid credentials, fix them
        if not credentials:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_json), SCOPES)
            credentials = flow.run_local_server(port=0)

        elif credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # Save back to disk
        with open(token_file, "wb") as f:
            pickle.dump(credentials, f)

        return build("youtube", "v3", credentials=credentials)

    def get_response_video_id(self, video_id: str | None, print_response: bool = False) -> dict:
        if video_id is None:
            print("Video ID is None")
            return {}
        response = self.youtube.videos().list(
            part="snippet,contentDetails,liveStreamingDetails",
            id=video_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        # if print_response:
        video_info = self.response_mng.get_video_info(response, print_response, True)
        if not video_info:
            return {}
        return response

    def get_channel_response(self, channel_id: str) -> dict | None:
        """Fetch the uploads playlist ID for a channel."""
        try:
            response = self.youtube.channels().list(
                part="contentDetails,snippet,statistics",
                id=channel_id
            ).execute()
            self.files_manager.add_to_today_quota(1)
            return response 
        except Exception as e:
            print(f"Error fetching channel {channel_id}: {e} \033[K")

    def get_all_playlists(self) -> list[dict[str,str]]:
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
                for item in response.get("items", []):
                    playlists.append({
                        "id": item["id"],
                        'publishedAt': item["snippet"]['publishedAt'],
                        "name": item["snippet"]["title"],
                        'itemCount':item['contentDetails']['itemCount']                     
                    })
                # Get the next page of results if available
                request = self.youtube.playlists().list_next(request, response)
            print("Retrieved all playlists successfully!\033[K")
            return playlists #The list is sorted by publishedAt. Desc
        except HttpError as e:
            print(f"An error occurred while getting all the Playlist: {e}\033[K")
            return []

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

    def get_all_ids_playlist(self, playlist_id: str | None, max_iterations: int = 5,
                             print_iterations: bool= False, count_repeated: bool = False) -> list:
        # The API only allows a max_iteration = 400
        if playlist_id is None:
            print('The Playlist ID is None. Doing Nothing')
            return []
        """Retrieve all video IDs from a playlist, handling pagination."""
        iterations = 0
        video_ids = []
        try:
            next_page_token = None
            while True:
                request = self.youtube.playlistItems().list(
                    part="id,snippet",
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
                print(f'There were {iterations} iterations in the process. The original number of iteration were {max_iterations}\033[K')
                print(f'There are {len(video_ids)} videos in the playlist')
            if count_repeated:
                counted_vids = Counter(video_ids)
                if any(c > 1 for c in counted_vids.values()):
                    print(f'Repeated elements in {yt_playlist}{playlist_id}\033[K')
                    for e, count in counted_vids.items():
                        if count > 1:
                            print(f'Repated {count}: {yt_url}{e}')
                            indexes = [str(index) for index, element in enumerate(video_ids,1) if element == e]
                            print(f'{e} => indexes {", ".join(indexes)}')
            return video_ids
        except HttpError as e:
            print(f"An error occurred while getting all the Playlist IDs {yt_playlist}{playlist_id}: \033[K\n{e}")
            return []
    
    def create_private_playlist(self, title: str, description: str) -> dict | None:
        """Create a private playlist on YouTube."""
        try:
            request = self.youtube.playlists().insert(
                part="snippet,status,contentDetails",
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
            print(f'Playlist "{title}" was created successfully!\033[K')
            print(f"Playlist ID: {response['id']}")
            print('-'*100)
   
            return response
        except HttpError as e:
            print(f"An error occurred while creating the playlist {title}: {e}")
            return None

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> dict | None:
        """Add a video to a playlist."""
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet,contentDetails",
                body={
                    "snippet": {
                        "playlistId": playlist_id,  # The ID of the playlist
                        "resourceId": {
                            "kind": "youtube#video",  # Specify the type as a YouTube video
                            "videoId": video_id,  # The ID of the video
                        },

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
                                       print_message: bool = True) -> dict | None:
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
            print("⚠️ Video not found in playlist.\033[K")
            print(f"{yt_url}{video_id_to_delete} not in {yt_playlist}{playlist_id}")
            return
   
    def get_response_channel_by_handle(self, handle: str) -> dict:
        handle = "@" + handle.replace('@', "")
        url = f"https://youtube.googleapis.com/youtube/v3/channels?forHandle={handle}&part=snippet,statistics,contentDetails&key={api_key}"
        response = requests.get(url)
        self.files_manager.add_to_today_quota(1)
        data = response.json()
        return data

    def get_response_from_playlist_id(self, playlist_id: str | None, print_response: bool = False) -> dict | None:
        if  playlist_id is None:
            print("The playlist ID is None. Doing Nothing.")
            return
        response = self.youtube.playlists().list(
            part="snippet,contentDetails,id",
            id=playlist_id).execute()

        self.files_manager.add_to_today_quota(1)
        if print_response:
            self.response_mng.get_playlist_info(response,True)
        return response

    def get_all_handles_from_playlist(self,
                                      playlist_id: str | None,
                                      delete_video: bool = False,
                                      print_handles: bool = False,
                                      sort_by_duration: bool = False,
                                      create_restricted_html: bool = False,
                                      iterations: int = 10) -> dict | None:
        if playlist_id is None:
            print('The playlist ID is None. Nothing is going to be done')
            return
        df = self.files_manager.YT_content_creators
        if playlist_id == 'LL':
            iterations = 6
        video_ids = self.get_all_ids_playlist(playlist_id, iterations)
        if not video_ids:
            return
        print(f'There are {len(video_ids)} in the playlist')
        handles_playlist = defaultdict(list)
        restricted_url = defaultdict(str)
        for index, video_id in enumerate(video_ids, 1):
            response = self.get_response_video_id(video_id)
            if response is None:
                continue
            restriction = self.response_mng.is_restricted(response)
            video_info = self.response_mng.get_video_info(response)
            if video_info is None:
                continue
            if restriction:
                print(f'The video ID: {video_id} is restricted. Index: {index}')
                self.response_mng.get_video_info(response, True)
                restricted_url[video_id] = video_info['title']
                print('-'*50)
            
            if not video_info:
                if delete_video:
                    self.delete_video_id_from_playlist(playlist_id, video_id)
                continue

            channelId = video_info.get('channelId', None)
            if channelId in df['channelId'].values:
                handle = df[df['channelId'] == channelId]['Handle'].iloc[0]
            elif channelId is None:
                print(f'Problem finding the channel ID{video_id}')
                continue

            else:
                channel_response = self.get_channel_response(channelId)
                if channel_response is None:
                    continue
                channel_info = self.response_mng.get_channel_info(channel_response)
                if not isinstance(channel_info, dict):
                    return
                
                handle = channel_info['customUrl']
            if video_info not in handles_playlist[handle]:
                handles_playlist[handle].append(video_info)
        if print_handles:
            align = max(len(h) for h in handles_playlist)
            zeros = len(str(max(len(handles_playlist[k]) for k in handles_playlist)))
            if sort_by_duration:
                sorted_handles = sorted(handles_playlist, key= lambda x: sum(dur.get('duration', 0) for dur in handles_playlist[x]), reverse=True)
            else:
                sorted_handles = sorted(handles_playlist, key= lambda x: len(handles_playlist[x]), reverse=True)
            for handle in sorted_handles:
                duration = sum(dur.get('duration', 0) for dur in handles_playlist[handle])
                print(f'{handle:<{align}} | {len(handles_playlist[handle]):0{zeros}d} | {duration_string(duration)}')
        if restricted_url and create_restricted_html:
            create_bookmarks(restricted_url, Path('Restricted.html'), yt_url, "Restricted URLs")
        
        return handles_playlist

    def get_playlist_duration(self) -> float | None:
        playlist_id = input("Playlist ID: ").strip()
        if 'youtube.com' in playlist_id:
            parsed = urlparse(playlist_id)
            query = parse_qs(parsed.query)
            playlist_ids = query.get("list")  # default to 0 if missing
            if not playlist_ids:
                print('There is no playlist ID in the URL')
                return None
            playlist_id = playlist_ids[0]
            
        playlist_response = self.get_response_from_playlist_id(playlist_id)
        if not isinstance(playlist_response, dict):
            print(f"There is no response for the playlist ID: {playlist_id}")
            return
        playlist_info = self.response_mng.get_playlist_info(playlist_response)

        if not isinstance(playlist_info, dict):
            print(f'There was not possible to get the info of the playlist {playlist_id}')
            return
        
        title = playlist_info['title']
        video_ids = self.get_all_ids_playlist(playlist_id, 100)
        if not isinstance(video_ids, list):
            print("")
            return
        total_duration = 0
        for index, video_id in enumerate(video_ids, 1):
            response = self.get_response_video_id(video_id)
            if response is None:
                return
            video_info = self.response_mng.get_video_info(response)
            if video_info is None:
                return
            if 'duration' not in video_info:
                print(f'{index} {yt_url}{video_id}')
                continue
            total_duration += video_info['duration']
        
        print(f'{title} => {len(video_ids)} | {duration_string(total_duration)}')
        return total_duration

    def get_video_ids_by_selection(self) -> None | list:
        options = ['Directly from YouTube',
                   'Watch Later',
                   'From File',
                   'From URL',
                   ]
        option_selected = choose_option(options, "Choose a Playlist")
        if option_selected is None:
            print('There is a problem in the selection')
            return
        elif option_selected == options[0]:
            playlist_list = self.get_all_playlists()
            if playlist_list is None:
                print('There was a problem getting all the Playlist')
                return
            playlist_names = [k.get('name', None) for k in playlist_list]
            playlist_name = choose_option(playlist_names, "Choose a Playlist:")
            playlist_id = next((d["id"] for d in playlist_list if playlist_name in d.values()), None)
            if playlist_id is None:
                print(f'There was a problem selecting the ID of the Playlist {playlist_name}')
                return
            print(f'The selected Playlist is {playlist_name}. Playlist ID: {playlist_id}')
            playlist_video_IDs = self.get_all_ids_playlist(playlist_id, 20)
            if not isinstance(playlist_video_IDs, list):
                return
            video_sorted = [{'video_id': video_id, 'index': f"{index:03d}"} for index, video_id in enumerate(playlist_video_IDs, 1)]
        elif option_selected == options[1]:
            playlist_video_IDs = self.get_all_ids_playlist(watch_later_id, 20)
            if playlist_video_IDs is None:
                print(f'There was a problem getting the Video IDs of the Watch Later Playlist ID: {watch_later_id}')
                return
            video_sorted = [{'video_id': video_id, 'index':  f"{index:03d}"} for index, video_id in enumerate(playlist_video_IDs, 1)]
        elif option_selected == options[2]:
            urls = self.files_manager.get_elements_from_file(Path('videos.txt'))
            video_sorted = []
            for index, url in enumerate(urls, 1):
                    parsed = urlparse(url)
                    query = parse_qs(parsed.query)
                    video_id = query.get("v", [0])[0]  # default to 0 if missing
                    # playlist = query.get("list", ["0"])[0] 
                    position = query.get("index", ["0"])[0]
                    video_info = {
                            'video_id': video_id,
                            'index': f'{int(position):03d}'
                    }
                    if video_info not in video_sorted:
                            # print(f'{index:02d} {video_id}')
                            video_sorted.append(video_info)       
        elif option_selected == options[3]:
            url = input('YouTube URL or Playlist ID: ').strip()
            playlist_id = get_playlist_id(url)
            playlist_video_IDs = self.get_all_ids_playlist(playlist_id, 10)
            if not isinstance(playlist_video_IDs, list):
                return
            video_sorted = [{'video_id': video_id, 'index':  f"{index:03d}"} for index, video_id in enumerate(playlist_video_IDs, 1)]
        else:
            print('There was problem and no option was selected')
            return
        return video_sorted

    def choose_parameter_playlist_id(self, message:str="Choose a Playlist",
                                     create_playlist: bool = False,
                                     ) -> dict[str,str | None] :
        playlists = self.get_all_playlists()
        if playlists:
            playlists.insert(0,{'name': "Watch Later", 'id': watch_later_id})
            playlist_names = [pl.get('name') for pl in playlists]
            new_playlist_str = 'Create new Playlist'
            if create_playlist:
                playlist_names.append(new_playlist_str)
            chosen_playlist = choose_option(playlist_names,message)
            if chosen_playlist == new_playlist_str:
                new_playlist = input("New Playlist Name: ").strip()
                response_playlist = self.create_private_playlist(new_playlist, new_playlist)
                if response_playlist:
                    playlist_id = response_playlist.get('id')
                    return {"playlist_id": playlist_id, "name": new_playlist}  #playlist_id
            else:
                playlist_id = next((d["id"] for d in playlists if chosen_playlist in d.values()), None)
                playlist_name = next((d["name"] for d in playlists if chosen_playlist in d.values()), None)
                return {"playlist_id": playlist_id, "name": playlist_name}

        return {"playlist_id": None, "name": None}

if __name__ =='__main__':
    yt = YouTubeManager()
    fm = filesManager()
    youtube = yt.youtube
    request = youtube.channels().list(
        part="contentDetails,snippet",
        mine=True,
        maxResults=50
    ).execute()
    fm.add_to_today_quota(1)
    print_dictionary(request)
    # resp_mng = response_manager()
    # fm = filesManager()
    # from API_KEY import watch_later_id 
    # from app_functions import (get_video_id)
    # clear_terminal()
    # selected = yt.choose_parameter_playlist_id(message="Choose a Playlist", create_playlist=False)
    # print(selected)

    # dict_functions = {
    #     "Get Handles for a Playlist: ": lambda: yt.get_all_handles_from_playlist(
    #                                             playlist_id= yt.choose_parameter_playlist_id().get('id'),
    #                                             delete_video = True,
    #                                             print_handles = True, 
    #                                             sort_by_duration = False, 
    #                                             create_restricted_html = True,
    #                                             iterations=10),
    #     "View repeated Video IDs in a playlist": lambda: yt.get_all_ids_playlist(
    #                                                     playlist_id = yt.choose_parameter_playlist_id().get('id'),
    #                                                     count_repeated = True),
    #     "Get a Video Response": lambda: yt.get_response_video_id(
    #                                     video_id=get_video_id(input("Video ID or URL: ")),
    #                                     print_response=True),
    #     "Print the Playlist Response": lambda: yt.get_response_from_playlist_id(
    #                                             playlist_id= yt.choose_parameter_playlist_id().get('id'),
    #                                             print_response=True),
        
    #     "Do nothing": None}
    # while True:
    #     choose_function = choose_option(list(dict_functions.keys()), f"Choose a Function")
    #     if choose_function:
    #         if dict_functions[choose_function] is None:
    #             print("Doing Nothing")
    #             break
    #         else:
    #             dict_functions[choose_function]()
    #     continue_option = choose_option([True, False], "Continue with another functionn: ")
    #     if not continue_option:
    #         break
        # clear_terminal()
        