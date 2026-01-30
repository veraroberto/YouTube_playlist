from YouTube import YouTubeManager
from response import response_manager
from filesManager import filesManager
from YouTube import yt_url

from app_functions import (choose_option,
                           duration_string)


from collections import defaultdict
import time

class PlaylistManager():
    
    def __init__(self):
        self.yt = YouTubeManager()
        self.response_mnr = response_manager()
        self.files_manager = filesManager()
        self.files_manager.YT_content_creators
        self.df = self.files_manager.YT_content_creators
        
        
    def move_video_to_playlist(self, quota_limit: int = 8000) -> None:
        
        playlist_handles = defaultdict(list)
        playlist_names =self.yt.get_all_playlists()
        playlist_chosen = choose_option(playlist_names, "Choose Origin Playlist")
        playlist_names.remove(playlist_chosen)
        source_id = playlist_chosen['id']
        source_name = playlist_chosen['name']
        sorted_keys = list(self.count_handles_playlist(source_id).keys())
        move_handles = []
        while True:
            choose_key = choose_option(sorted_keys, "Choose a Handle to move")
            sorted_keys.remove(choose_key)
            move_handles.append(choose_key)
            if not choose_option([True, False], "Continue with the selection to move Handles: "):
                break
        print(f'Moving the following handles: {", ".join(sorted(move_handles, key=str.lower))}')
        another_options = ['Create New Playlist', 'Do nothing and Exit']
        playlist_names.extend(another_options)
        destination = choose_option(playlist_names, "Choose Destination Playlist")
        
        if destination == another_options[0]:
            destination_name = input('Name of the new Playlist: ')
            print(f'Creating Playlist: {destination_name}')
            response_ch = self.yt.create_private_playlist(destination_name, destination_name)
            if response_ch is None:
                print('Imposible to create the new Playlist. Exiting the moving process')
                return
            destination_id = response_ch.get('id', None)
            if destination_id is None:
                print('Imposible to get the new Playlist ID. Exiting the moving process')
                return
        elif destination == another_options[1]:
            print('Doing nothing')
            return
        else:
            destination_id = destination['id']
            destination_name = destination['name']
        print(f'Destination playlist is {destination_name} with the ID is {destination_id}')
        num_videos = sum(len(playlist_handles[handle]) for handle in move_handles)
        to_consume = num_videos * 101 # 1 quota min to find the video in the playlist. 50 to delete and 50 to add 
        current_quota = self.files_manager.get_today_quota()
        message_parts =  [f"Are you sure you want to continue.",
                          f"There are {num_videos} videos to move and",
                          f"its goint to take at least {to_consume:,} quotas.",
                          f"The final quota is going to be aproximately: {current_quota + to_consume:,}."]
        if not choose_option([True, False]," ".join(message_parts)): 
            print('Not moving any video')
            return
        start_moving = time.time()
        for i, h in enumerate(move_handles, 1):
            print(f'Moving the videos from {h}')
            video_ids = playlist_handles[h]
            for video_id_to_move in video_ids:
                # print(f'{i:02d} {video_id}')
                if self.files_manager.get_today_quota() > quota_limit:
                    print(f"Stopping the Processs to prevent the quota surpass {quota_limit:,}")
                    return
                if self.yt.delete_video_id_from_playlist(source_id, video_id_to_move, print_message = False) is None:
                    print(f"There is a problem deleting {video_id_to_move} from {source_name}. Stopping Everything.")
                    return
                if self.yt.add_video_to_playlist(destination_id, video_id_to_move) is None:
                    print(f"There is a problem adding {video_id_to_move} to {destination_name}. Stopping Everything.")
        total_duration = time.time() - start_moving
        print(f'Total duration of the moving process => {duration_string(total_duration)}')      

    def count_handles_playlist(self, playlist_id: str) -> dict:
        playlist_handle = defaultdict(list)
        video_ids = self.yt.get_all_ids_playlist(playlist_id, 20)
        for video_id in video_ids:
            response = self.yt.get_response_video_id(video_id)
            video_info = self.response_mnr.get_video_info(response)
            channelId = video_info['channelId']
            if channelId in self.df['channelId'].values:
                handle = self.df[self.df['channelId'] == channelId]['Handle'].iloc[0]
            else:
                handle = 'Not in DF'
            playlist_handle[handle].append(response)
        
        sorted_handels = sorted(playlist_handle, key= lambda x: len(playlist_handle[x]), reverse=True)
        align = max(len(key) for key in playlist_handle) + 1
        align_num = len(str(max(len(playlist_handle[h]) for h in playlist_handle)))
        for h in sorted_handels:
            label = f"{h}:".ljust(align)
        # 3. Get the count as a string and use .rjust() to align it to the right
            count = str(len(playlist_handle[h])).rjust(align_num)
            
            print(f"{label} {count}")

        return playlist_handle
    


if __name__ =='__main__':
    import json
    pm = PlaylistManager()
    response_mng = response_manager()
    # playlist_id = 'PLpLSuxy9E5PzxURBwG1_KnFrp5hDrVMr0'
    # pm.count_handles_playlist(playlist_id)
    # pm.move_video_to_playlist(6500) 
    # playlist_id = 'PLpLSuxy9E5Pw3e_W2DwHvh2z3KTjL5ZKE'

    # response_dict = pm.count_handles_playlist(playlist_id)
    # file_path = 'Cine_Playlist.json'
    # with open(file_path, 'w', encoding="utf-8") as json_file:
    #     json.dump(response_dict, json_file, indent=4)
    # with open(file_path, mode = 'r', encoding="utf-8") as json_file:
    #     playlists_names = json.load(json_file)
    # # print(playlists.keys())
    # align = max(len(playlist) for playlist in playlists_names)
    # playlists_names_sort = sorted(playlists_names, key = lambda x: len(playlists_names[x]), reverse=True)
    # for playlist in playlists_names_sort:
    #     responses = playlists_names[playlist]
    #     # label = f'{playlist}:'.ljust(align + 1)
    #     # count = f'{len(responses)}'.rjust(2)
    #     # print(f'{label} {count}')

    #     print(playlist)
    #     for response in responses:
    #         video_info = response_mng.get_video_info(response)
    #         title = video_info['title']
    #         publishedAt = video_info['publishedAt']
    #         video_id = video_info['video_id']
    #         message = f"{yt_url}{video_id}: {publishedAt} {title[0:70]}"
    #         print(message[0:114])
    #     print('*'*50)

      


        