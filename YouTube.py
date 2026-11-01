import pickle, time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from API_KEY import (api_key,
                    #  watch_later_id,
                     )
import requests, re
from datetime import date, datetime
from collections import Counter
from pathlib import Path
from colors import Color

from app_functions import (create_bookmarks,
                           duration_string,
                           choose_option,
                           get_playlist_id,
                           get_video_id,
                           clear_terminal,
                           pluralize,
                           print_dictionary
                           )

from filesManager import filesManager
from collections import defaultdict
from paths import (tokens_folder,
                   playlist_folder)


from urllib.parse import (urlparse,
                          parse_qs)
from response import response_manager
from paths import (yt_url,
                   yt_playlist,
                   yt_channel,
                   shorts_playlist_name,
                   other_playlist_name)

default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published
quota_limit = 9900 # I set at this value since sometime the API doesn't allow for more request when you are to close to the limit.
handles_base_filename = f'all_handles_in_playlist.json'
class YouTubeManager:

    def __init__(self):
        # 1. Store the paths
        self.files_manager = filesManager()
        self.response_mng = response_manager()
        self.color = Color()

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

    def get_response_video_id(self, video_id: str | None, print_response: bool = False, show_error: bool = False) -> dict:
        if video_id is None:
            print("Video ID is None")
            return {}
        response = self.youtube.videos().list(
            part="snippet,contentDetails,liveStreamingDetails,statistics,status",
            id=video_id
        ).execute()
        self.files_manager.add_to_today_quota(1)
        video_info = self.response_mng.get_video_info(response, print_response, del_extra_keys=True)
        if not video_info:
            if show_error:
                print(f"Video ID {self.color.format(str(video_id), self.color.RED, self.color.BOLD)} doesn't have a response")
                print_dictionary(response)
                print('*'*50)
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
        items_responses = []
        try:
            next_page_token = None
            while True:
                request = self.youtube.playlistItems().list(
                    part="id,snippet,contentDetails,status",
                    playlistId=playlist_id,
                    maxResults=50,  # Maximum number of items per request
                    pageToken=next_page_token  # Handle pagination
                )
                response = request.execute()
                self.files_manager.add_to_today_quota(1)

                # Extract video IDs from the response
                for item in response.get("items", []):
                    snippet = item.get('snippet', {})
                    videoOwnerChannelTitle = snippet.get('videoOwnerChannelTitle')
                    videoOwnerChannelId = snippet.get('videoOwnerChannelId')
                    publishedAt = snippet.get('publishedAt', default_date)
                    position = snippet.get('position', 0)
                    contentDetails = item.get('contentDetails', {})
                    videoId = contentDetails.get('videoId')
                    status = item.get('status', {})
                    privacyStatus = status.get('privacyStatus')
                    item_response = {'videoOwnerChannelTitle': videoOwnerChannelTitle,
                                     'videoOwnerChannelId': videoOwnerChannelId,
                                     'publishedAt': publishedAt,
                                     'position': position,
                                     'videoId': videoId,
                                     'privacyStatus': privacyStatus}
                    items_responses.append(item_response)
                    # print(f'snippet keys: {snippet.keys()}')
                    # print(f'id keys: {item["id"]}')
                    # print(f'contentDetails keys {contentDetails.keys()}')
                    # print(f'status keys {status.keys()}')
                    # print_dictionary(item_response)
                    # print('-'*50)
                    # video_ids.append(item["snippet"]["resourceId"]["videoId"])

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
                video_ids = [r.get('videoId') for r in items_responses]
                counted_vids = Counter(video_ids)
                if any(c > 1 for c in counted_vids.values()):
                    print(f'Repeated elements in {yt_playlist}{playlist_id}\033[K')
                    for e, count in counted_vids.items():
                        if count > 1:
                            print(f'Repated {count}: {yt_url}{e}')
                            indexes = [str(index) for index, element in enumerate(items_responses,1) if element == e]
                            print(f'{e} => indexes {", ".join(indexes)}')
            return items_responses
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
                                      iterations: int = 10,
                                      print_message: bool = False,
                                      delete_no_response_video: bool = False) -> dict:
        if playlist_id is None:
            print('The playlist ID is None. Nothing is going to be done')
            return {}
        df = self.files_manager.YT_content_creators
        if playlist_id == 'LL':
            iterations = 6
                                                        
        item_responses = self.get_all_ids_playlist(playlist_id, 100)
        if not item_responses:
            return {}
        video_ids = [item.get('videoId') for item in item_responses]

        if print_message:
            print(f'{self.color.CLEAR_LINE}There are {len(video_ids)} in the playlist', end='\r')
        handles_playlist = defaultdict(list)
        restricted_url = defaultdict(str)
        for index, video_id in enumerate(video_ids, 1):
            response = self.get_response_video_id(video_id)
            restriction = self.response_mng.is_restricted(response)
            video_info = self.response_mng.get_video_info(response)
            if not response or not video_info:
                print(f"{yt_playlist}{playlist_id}\nThere was a problem getting the response for the video ID: {video_id}. Index: {index}\033[K")
                if delete_no_response_video:
                    self.delete_video_id_from_playlist(playlist_id=playlist_id,
                                                       video_id_to_delete=video_id,
                                                       print_message=True)
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
                    continue

                handle = channel_info['customUrl']
            if video_info not in handles_playlist[handle]:
                handles_playlist[handle].append(video_info)
        if print_handles:
            self.print_dict_response_videos(handles_playlist, sort_by_duration=sort_by_duration)
        if restricted_url and create_restricted_html:
            create_bookmarks(restricted_url, Path('Restricted.html'), yt_url, "Restricted URLs")

        return handles_playlist
    
    def print_dict_response_videos(self, handles_dict: dict, sort_by_duration: bool = False) -> None:
        if not handles_dict:
            print('The handles dictionary is empty. Nothing to print')
            return
        align = max(len(h) for h in handles_dict)
        zeros = len(str(max(len(handles_dict[k]) for k in handles_dict)))
        if sort_by_duration:
            sorted_handles = sorted(handles_dict, key= lambda x: sum(dur.get('duration', 0) for dur in handles_dict[x]), reverse=True)
        else:
            sorted_handles = sorted(handles_dict, key= lambda x: len(handles_dict[x]), reverse=True)
        total_duration = 0
        for handle in sorted_handles:
            duration = sum(dur.get('duration', 0) for dur in handles_dict[handle])
            total_duration += duration
            print(f'{handle:<{align}} | {len(handles_dict[handle]):0{zeros}d} | {duration_string(duration)}')
        total_videos = sum(len(handles_dict[k]) for k in handles_dict)
        
        print(f'{self.color.BLUE}{self.color.BOLD}There are a total of {total_videos} {pluralize(total_videos, "video", "videos")}',
              f' in all the playlists.{self.color.RESET}',
              f'Duration all playlist => {self.color.format(duration_string(total_duration), self.color.BOLD, self.color.UNDERLINE)}')

    def print_dict_response_videos_files(self) -> None:
        dictionaries = {file.stem: file for file in Path.cwd().rglob(f"*{handles_base_filename}")}
        if not dictionaries:
            print("There are not json file in the current folder")
            return
        while True:
            choose_dictionary = choose_option(list(dictionaries.keys()), "Choose a File to printh the handles")
            if dictionaries[choose_dictionary]:
                dictionary = self.files_manager.read_json(dictionaries[choose_dictionary])
                sort_by_duration = choose_option([True, False], f"Print by Duration {choose_dictionary}")
                self.print_dict_response_videos(dictionary, sort_by_duration = sort_by_duration)
            if not choose_option([True, False], "Print another Handles file"):
                break
            clear_terminal()

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
        item_responses = self.get_all_ids_playlist(playlist_id, 100)
        video_ids = [item.get('videoId') for item in item_responses]
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
            item_responses = self.get_all_ids_playlist(playlist_id, 20)
            if not item_responses:
                return
            playlist_video_IDs = [item.get('videoId') for item in item_responses]
            video_sorted = [{'video_id': video_id, 'index': f"{index:03d}"} for index, video_id in enumerate(playlist_video_IDs, 1)]

        elif option_selected == options[1]:
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
        elif option_selected == options[2]:
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
            # playlists.insert(0,{'name': "Watch Later", 'id': watch_later_id})
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

    def get_subs_not_in_df(self) -> list:
        df = self.files_manager.YT_content_creators
        channelId_df = df['channelId'].values   
        subscriptions = self.get_subscriptions()
        not_in_df = []
        channel_subscribed = []
        for sub in subscriptions:
            snippet = sub.get('snippet', {})
            resourceId = snippet.get('resourceId', {})
            channelId = resourceId.get('channelId', {})     
            title = snippet.get('title') 
            
            channel_subscribed.append({'channelId':channelId, 'title': title})   
            if channelId not in channelId_df:
                not_in_df.append({'title': title, 'channelId':channelId})
        
        if not_in_df:
            print(f'{self.color.format("Subscriptions not in DF", self.color.BLUE, self.color.BOLD)}')
            for s in not_in_df:
                print(s['title'])
                print(f"{yt_channel}{s['channelId']}")
                print('*'*75)
        else:
            print("All subscritpions are in the DataFrame")

        missing_sub_df = []
        for channelId in channelId_df:#:
            channelID_subscribed = next((d["channelId"] for d in channel_subscribed if channelId in d.values()), None)
            uploads = str(df[df['channelId'] == channelId]['uploads'].iloc[0])
            if not channelID_subscribed and not uploads.startswith('PL'):
                row = df[df['channelId'] == channelId].iloc[0].to_dict()
                print(channelID_subscribed)
                print_dictionary(row)
                print('-'*75)
                missing_sub_df.append(channelId)
        
        if missing_sub_df:
            digits = len(str(len(missing_sub_df)))
            print(f'{self.color.format("Channel ID in DF not subscribed", self.color.RED, self.color.BOLD)}')
            for index, channelId in enumerate(missing_sub_df, 1):
                print(f'{index:0{digits}d} {yt_channel}{channelId}')

    def get_video_response_all_playlists(self):
        start = time.time()
        playlists = [file.stem.replace('_', ' ') for file in playlist_folder.iterdir() if file.suffix.lower() == '.txt']
        playlists.extend([other_playlist_name,shorts_playlist_name])
        playlist_info = self.get_all_playlists()
        youtube_playlists = defaultdict(list)
        num_playlist = len(playlists)
        digitis = len(str(num_playlist))
        total_videos = 0
        for index, playlist_name in enumerate(playlists, 1):
            playlist_id = next((d["id"] for d in playlist_info if playlist_name in d.values()), None)
            if playlist_id:
                print(f'{self.color.CLEAR_LINE}{index:0{digitis}d} / {num_playlist} {self.color.format(playlist_name, self.color.GREEN, self.color.BOLD)}', end='\r')
                item_responses = self.get_all_ids_playlist(playlist_id=playlist_id,
                                          max_iterations=20,
                                          print_iterations=False,
                                          count_repeated=True)

                if not item_responses:
                    return
                video_ids = [item.get('videoId') for item in item_responses]
                for video_id in video_ids:
                    response = yt.get_response_video_id(video_id=video_id, print_response=False, show_error=False)
                    if response:
                        youtube_playlists[playlist_name].append(self.response_mng.get_video_info(response))

                total_videos += len(video_ids)
        today = date.today()
        formatted_date = today.strftime("%Y_%m_%d")
        duration = duration_string(time.time() - start)
        print(f'{self.color.CLEAR_LINE}{self.color.BLUE}There are {total_videos} {pluralize(total_videos, "video")} in all the Playlists{self.color.RESET}.',
              f'Duration process => {self.color.format(duration, self.color.BOLD, self.color.UNDERLINE)}')
        self.files_manager.write_json(youtube_playlists, f'{formatted_date}_all_responses_playlists.json')
        return youtube_playlists
    
    def get_handles_from_all_playlists(self, dictionary: dict[str:list]) -> dict[str:list]:
        df = self.files_manager.YT_content_creators
        handles = defaultdict(list)
        handles_not_in_df = set()
        for responses in dictionary.values():
            for video_info in responses:
                channelId = video_info.get('channelId', "No Avilable")
                channelTitle = video_info.get('channelTitle')
                channelTitle_vevo = re.sub('vevo', "", channelTitle, flags=re.IGNORECASE)
                if channelId in df['channelId'].values:
                    handle = df[df['channelId'] == channelId]['Handle'].iloc[0]
                elif channelTitle_vevo in df['channelTitle'].values:
                    handle = df[df['channelTitle'] == channelTitle_vevo]['Handle'].iloc[0]
                    print(f'{self.color.RED}{handle} was found by removing vevo from {channelTitle} in the colum channelTitle {self.color.RESET}')
                elif channelTitle_vevo.lower() in df['Handle'].values:
                    handle = channelTitle_vevo.lower()
                    print(f'{handle} was found by removing vevo from {channelTitle} in the colum Handle')
                else:
                    handle = channelId
                    handles_not_in_df.add(channelId)
                handles[handle].append(video_info)
        if handles_not_in_df:
            print(f'{self.color.format("Channel IDs not in the Data Frame", self.color.YELLOW, self.color.BOLD)}')
            for i, channel in enumerate(handles_not_in_df, 1):
                channel_resposne = self.get_channel_response(channel_id=channel)
                response_channel = self.response_mng.get_channel_info(channel_response=channel_resposne)
                handle = response_channel.get('customUrl', channelId)
                if handle != channel:
                    handles[handle].extend(handles[channel])
                    del handles[channel]
                else:
                    print(f'Handle not found for {yt_channel}{channel}')
                print(f'{i} {handle} {yt_channel}{channel}')
        today = date.today()
        formatted_date = today.strftime("%Y_%m_%d")
        self.files_manager.write_json(handles,f"{formatted_date}_{handles_base_filename}")
        return handles

    def get_personal_info_YouTube(self) -> None:
        dict_functions = {
            "Get Handles for a Playlist: ": lambda: self.get_all_handles_from_playlist(
                                                    playlist_id= yt.choose_parameter_playlist_id().get('playlist_id'),
                                                    delete_video = True,
                                                    print_handles = True,
                                                    sort_by_duration = True,
                                                    create_restricted_html = True,
                                                    iterations=10,
                                                    delete_no_response_video = True),
            "View repeated Video IDs in a playlist": lambda: self.get_all_ids_playlist(
                                                            playlist_id = yt.choose_parameter_playlist_id().get('id'),
                                                            count_repeated = True),
            "Get a Video Response": lambda: self.get_response_video_id(
                                            video_id=get_video_id(input("Video ID or URL: ")),
                                            print_response=True,
                                            show_error=True),
            "Print the Playlist Response": lambda: self.get_response_from_playlist_id(
                                                    playlist_id= yt.choose_parameter_playlist_id().get('id'),
                                                    print_response=True),
            # "Get the Handles from all the Playlists": lambda: self.get_handles_from_all_playlists(),
            # "Print the Handles already in a File": lambda: self.print_handles_from_files(),
            "Get the Subsriptions that are not in DF": lambda: self.get_subs_not_in_df(),
            "Do nothing": None}
        while True:
            choose_function = choose_option(list(dict_functions.keys()), f"Choose a Function")
            if choose_function:
                if dict_functions[choose_function] is None:
                    print("Doing Nothing")
                    break
                else:
                    dict_functions[choose_function]()
            continue_option = choose_option([True, False], "Continue with another functionn: ")
            if not continue_option:
                break


if __name__ =='__main__':
    yt = YouTubeManager()
    fm = filesManager()
    clear_terminal()
    dictionary = yt.get_video_response_all_playlists()
    handles_dictionary = yt.get_handles_from_all_playlists(dictionary)
    # handles_dictionary = fm.read_json('2026_10_30_all_handles_in_playlist')
    yt.print_dict_response_videos(handles_dict=handles_dictionary, sort_by_duration=True)
    # # yt.get_personal_info_YouTube()
    fm.get_today_quota(print_statement=True)


    

