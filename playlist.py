from YouTube import YouTubeManager
from response import response_manager
from filesManager import filesManager

from app_functions import (choose_option,
                           duration_string)


from collections import defaultdict
import time

class PlaylistManager():
    
    def __init__(self):
        self.yt = YouTubeManager()
        self.respons_mnr = response_manager()
        self.files_manager = filesManager()
        self.files_manager.YT_content_creators
        self.df = self.files_manager.YT_content_creators
        self.playlist_names =self.yt.get_all_playlists()
        
    def move_video_to_playlist(self) -> None:
        quota_limit = 8000
        playlist_handles = defaultdict(list)   
        playlist_choosen = choose_option(self.playlist_names, "Choose Origin Playlist")
        self.playlist_names.remove(playlist_choosen)
        source_id = playlist_choosen['id']
        source_name = playlist_choosen['name']
        print(source_id)
        print(source_name)
        # playlist_id = playlist_choosen['id']
        # video_ids = self.yt.get_all_ids_playlist(playlist_id,200)
        # for video_id in video_ids:
        #     response = self.yt.get_response_video_id(video_id)
        #     video_info = self.respons_mnr.get_video_info(response)
        #     channelId = video_info['channelId']

        #     if channelId in self.df['channelId'].values:
        #         handle = self.df[self.df['channelId'] == channelId]['Handle'].iloc[0]
        #     else:
        #         response_channel = self.yt.get_channel_response(channelId)
        #         items = response_channel.get('items', [])
        #         if not items:
        #             continue
        #         snippet = items[0].get('snippet', {})
        #         handle = snippet.get('customUrl', '').replace('@', '')
        #     playlist_handles[handle].append(video_id)
        # sorted_keys = sorted(playlist_handles, key=lambda x: len(playlist_handles[x]), reverse=True)
        # alignment_key = max(len(key) for key in playlist_handles)
        # alignment_val = max(len(str(len(v))) for v in playlist_handles.values())
        # for key in sorted_keys:
        #     key_string = f'{key}:'
        #     print(f'{key_string:<{alignment_key + 1}} {len(playlist_handles[key]):>{alignment_val}}')
        sorted_keys = self.count_handles_playlist(source_id)
        move_handles = []
        while True:
            choose_key = choose_option(sorted_keys, "Choose a Handle to move")
            sorted_keys.remove(choose_key)
            move_handles.append(choose_key)
            if not choose_option([True, False], "Continue with the selection to move Handles: "):
                break
        print(f'Moving the following handles: {", ".join(sorted(move_handles, key=str.lower))}')
        another_options = ['Create New Playlist', 'Do nothing and Exit']
        self.playlist_names.extend(another_options)
        destination = choose_option(self.playlist_names, "Choose Destination Playlist")
        
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
                if self.yt.delelte_video_id_from_playlist(source_id, video_id_to_move, print_message = False) is None:
                    print(f"There is a problem deleting {video_id_to_move} from {source_name}. Stopinng Everythin.")
                    return
                if self.yt.add_video_to_playlist(destination_id, video_id_to_move) is None:
                    print(f"There is a problem adding {video_id_to_move} to {destination_name}. Stopinng Everythin.")
        total_duration = time.time() - start_moving
        print(f'Total duration of the moving process => {duration_string(total_duration)}')      

    def count_handles_playlist(self, playlist_id: str) -> None:
        playlist_handle = defaultdict(list)
        # Select the Playlist
        # names = [p['name'] for p in self.playlist_names]
        # playlist = choose_option( names, "Select the Playlist to count: ")
        # playlist_id = self.playlist_names[names.index(playlist)]['id']
        # # print(playlist)
        # print(playlist_id)
        video_ids = self.yt.get_all_ids_playlist(playlist_id, 20)
        for video_id in video_ids:
            response = self.yt.get_response_video_id(video_id)
            video_info = self.respons_mnr.get_video_info(response)
            channelId = video_info['channelId']
            if channelId in self.df['channelId'].values:
                handle = self.df[self.df['channelId'] == channelId]['Handle'].iloc[0]
            else:
                handle = 'Not in DF'
            playlist_handle[handle].append(video_id)
        
        sorted_handels = sorted(playlist_handle, key= lambda x: len(playlist_handle[x]), reverse=True)
        align = max(len(key) for key in playlist_handle) + 1
        align_num = len(str(max(len(playlist_handle[h]) for h in playlist_handle)))
        for h in sorted_handels:
            label = f"{h}:".ljust(align)
        # 3. Get the count as a string and use .rjust() to align it to the right
            count = str(len(playlist_handle[h])).rjust(align_num)
            
            print(f"{label} {count}")

        return sorted_handels
if __name__ =='__main__':
    pm = PlaylistManager()
    # playlist_id = 'PLpLSuxy9E5PzxURBwG1_KnFrp5hDrVMr0'
    # pm.count_handles_playlist(playlist_id)
    pm.move_video_to_playlist()


        