from filesManager import filesManager
from YouTube import YouTubeManager
from response import response_manager


from app_functions import choose_option, remove_accents
from manage_video_ids import get_video_id, get_playlist_id

from pathlib import Path
import pandas as pd

class df_manager:
    columns = ['Handle', 'channelName', 'channelId', 'uploadsID']
    def __init__(self):
        self.files_manager = filesManager()
        self.yt = YouTubeManager()
        self.response_mgr = response_manager()
        self.file_path_yt_creators = self.files_manager.file_path_yt_creators
        self.playlist_folder = self.files_manager.playlist_folder
        if self.file_path_yt_creators.exists():
            self.YT_content_creators = pd.read_csv(self.file_path_yt_creators)
        else:
            self.YT_content_creators = pd.DataFrame(columns=self.columns)

        self.playlist_folder = self.files_manager.playlist_folder

        self.playlist_files = [file for file in self.playlist_folder.iterdir() if file.suffix == '.txt']
        self.playlist_names = [playlist.stem.replace('_', ' ').strip() for playlist in self.playlist_files]


    def add_row_df(self):
        options = ['Video ID',
                   'Handle',
                   'Channel ID',
                   'Playlist ID']
        chosen = choose_option(options, "Add row by")

        if chosen == options[0]: # Video ID
            video_id = get_video_id(input("Video ID or the URL of the channel: ").strip())
            response = self.yt.get_response_video_id(video_id)
            video_info = self.response_mgr.get_video_info(response)
            channelId = video_info['channelId']
            channel_response = self.yt.get_channel_response(channelId)
            info_df = self.response_mgr.get_channel_info(channel_response)          
            
        elif chosen == options[1]: # Handle
            handle = remove_accents(input("New Handle: ").replace('@', "").lower().strip())
            if handle in self.YT_content_creators['Handle'].values:
                print(f'Handle {handle} is already in the DataFrame')
                return
            else:
                print(f'{handle} is going to be added to the Data Frame')
                channel_response = self.yt.get_response_channel_by_handle(handle)
                info_df = self.response_mgr.get_channel_info(channel_response)
        elif chosen == options[2]: # Channel ID
            channelId = input('Add a new Row by channelId: ')
            if channelId in self.YT_content_creators['channelId'].values:
                print(f"The channelId {channelId} is already in the Data Frame")
                return
            else:
                channel_response = self.yt.get_channel_response(channelId)
                info_df = self.response_mgr.get_channel_info(channel_response) 

        elif chosen == options[3]: # Playlist 
            playlist_id =  get_playlist_id(input('Get the new playlist ID: ').strip())
            if playlist_id in self.YT_content_creators['uploadsID'].values:
                print(f'The Playlist {playlist_id} ID is already in the DF')
                return
            else:
                playlist_response = self.yt.get_response_from_playlist_id(playlist_id)
                info_df = self.response_mgr.get_playlist_info(playlist_response)

        # info_df
        handle = info_df['customUrl']
        channelTitle = info_df['channelTitle']
        channelId = info_df['channelId']
        uploads = info_df['uploads']   
        
        print(info_df)
        return

        #Sort the new row into a Playlist
        # playlists_info = self.yt.get_all_playlists()
        self.playlist_names.extend(['Other Videos', "New Playlist"])
        handle_playlist = choose_option(self.playlist_names, f"Add the new {chosen} to the Playlist:")
        if handle_playlist == self.playlist_names[-2]:
            print(f'{chosen} is not going to be added to any particular playlist')
        elif handle_playlist == self.playlist_names[-1]:
            new_playlist_name = input('Name of the New Playlist: ').strip()
            playlist_file_path = self.files_manager.playlist_folder / f'{handle_playlist}.txt'
            if playlist_file_path.exists():
                print(f'The new Playlist: {new_playlist_name} is already in the files.')
            else:
                  self.files_manager.add_element_to_file(playlist_file_path, handle, sort_list=False, print_statement=False)
        else:
            playlist_file_path = self.files_manager.playlist_folder / f'{handle_playlist.replace(" ","_")}.txt'
            self.files_manager.add_element_to_file(playlist_file_path, handle, sort_list=False)

        

        video_ids_yt = self.yt.get_all_ids_playlist(uploads)
        if video_ids_yt:    
        # print(f'Time getting the video ids: {duration_string(time.time() - inicio)}')

            #Add the Videos IDs of the new row to the txt files
            file_path_video_ids = self.files_manager.content_creator_folder / f'{handle}.txt'
            print(f'{handle} has {len(video_ids_yt):,} videos')
            elements_video_ids = video_ids_yt[1:]
            self.files_manager.add_list_to_file(file_path_video_ids, elements_video_ids, sort_list=False, create_file=True)

        # Adding the new row
        new_row = handle, channelTitle, channelId, uploads
        self.YT_content_creators.loc[len(self.YT_content_creators)] = new_row
        self.YT_content_creators.sort_values(by='Handle', inplace = True,  key=lambda col: col.str.lower())
        self.YT_content_creators.reset_index(drop=True, inplace=True)
        self.files_manager.write_csv_safely(self.YT_content_creators, self.file_path_yt_creators)

if __name__ == "__main__":
    test = df_manager()
    test.add_row_df()
    
