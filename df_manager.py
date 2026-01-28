from filesManager import filesManager
from YouTube import YouTubeManager
from response import response_manager


from app_functions import choose_option, remove_accents
from manage_video_ids import get_video_id, get_playlist_id
from paths import playlist_folder, exception_folder, content_creator_folder
# from manage_video_ids import manage_exceptions

from pathlib import Path
import pandas as pd


from paths import columns_df


class df_manager:
    
    def __init__(self):
        self.files_manager = filesManager()

        self.file_path_yt_creators = self.files_manager.file_path_yt_creators
        if self.file_path_yt_creators.exists():
            self.YT_content_creators = pd.read_csv(self.file_path_yt_creators)
        else:
            self.YT_content_creators = pd.DataFrame(columns=columns_df)

        self.playlist_files = [file for file in playlist_folder.iterdir() if file.suffix == '.txt']
        self.playlist_names = [playlist.stem.replace('_', ' ').strip() for playlist in self.playlist_files]

        self.yt = YouTubeManager()
        self.response_mgr = response_manager()

    def add_row_df(self) -> None:
        options = ['Video ID',
                   'Handle',
                   'Channel ID',
                   'Playlist ID']
        chosen = choose_option(options, "Add row by")

        if chosen == None:
            return
        elif chosen == options[0]: # Video ID
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
            if playlist_id in self.YT_content_creators['uploads'].values:
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

        #Sort the new row into a Playlist
        self.playlist_names.extend(['Other Videos', "New Playlist"])
        handle_playlist = choose_option(self.playlist_names, f"Add the new {chosen} to the Playlist:")
        if handle_playlist == self.playlist_names[-2]:
            print(f'{chosen} is not going to be added to any particular playlist')
        elif handle_playlist == self.playlist_names[-1]:
            new_playlist_name = input('Name of the New Playlist: ').strip()
            playlist_file_path = playlist_folder / f'{handle_playlist}.txt'
            if playlist_file_path.exists():
                print(f'The new Playlist: {new_playlist_name} is already in the files.')
            else:
                  self.files_manager.add_element_to_file(playlist_file_path, handle, sort_list=False, print_statement=False)
        else:
            playlist_file_path = playlist_folder / f'{handle_playlist.replace(" ","_")}.txt'
            self.files_manager.add_element_to_file(playlist_file_path, handle, sort_list=False)
        video_ids_yt = self.yt.get_all_ids_playlist(uploads, 200)
        if video_ids_yt:    
        # print(f'Time getting the video ids: {duration_string(time.time() - inicio)}')

            #Add the Videos IDs of the new row to the txt files
            file_path_video_ids = content_creator_folder / f'{handle}.txt'
            print(f'{handle} has {len(video_ids_yt):,} videos')
            elements_video_ids = video_ids_yt[1:]
            self.files_manager.add_list_to_file(file_path_video_ids, elements_video_ids, sort_list=False, create_file=True)

        # Adding the new row
        new_row = handle, channelTitle, channelId, uploads
        self.YT_content_creators.loc[len(self.YT_content_creators)] = new_row
        self.YT_content_creators.sort_values(by='Handle', inplace = True,  key=lambda col: col.str.lower())
        self.YT_content_creators.reset_index(drop=True, inplace=True)
        self.files_manager.write_csv_safely(self.YT_content_creators, self.file_path_yt_creators)
        
        if choose_option([True, False], "Add an exception: "):
            exception_files = [file.stem for file in exception_folder.iterdir() if file.suffix =='.txt']
            print(exception_files)
            while True:
                file = choose_option(exception_files, "Choose the to Exception file to add the Handle")
                file_path = exception_folder / f'{file}.txt'
                self.files_manager.add_element_to_file(file_path, handle, sort_list=True, print_statement=False)
                
                if not choose_option([True, False], "Continue Adding Exception: "):
                    break
                exception_files.remove(file)

    def delete_information_in_files(self) -> None:
        handle = remove_accents(input('Select a handle to delete: ').strip().lower())
        # Folders
        # content_creator_folder = self.files_manager.content_creator_folder
        if handle not in self.YT_content_creators['Handle'].values:
            print(f'The handle {handle} is not in the DF')
            # return
        else:
            self.YT_content_creators = self.YT_content_creators[self.YT_content_creators['Handle'] != handle]
            self.YT_content_creators.sort_values(by='Handle', inplace = True,  key=lambda col: col.str.lower())
            self.YT_content_creators.reset_index(drop=True, inplace=True)
            self.files_manager.write_csv_safely(self.YT_content_creators, self.file_path_yt_creators)
            print(f'{handle} was removed from the Data Frame')
        
        for file_handle in Path.cwd().rglob('*'):
            if file_handle.stem == handle:
                try:
                    file_handle.unlink()
                    print(f'The file {file_handle.name} was deleted')
                except Exception as e:
                    print(f'The file {file_handle.name} does not exists. The error is {e}')

        # Remove handle from all the txt files
        search_folder = [
            playlist_folder,
            exception_folder,
        ]
        files = [file  for folder in search_folder for file in folder.iterdir() if file.suffix =='.txt']

        found_handle = False
        for file in files:
            content = file.read_text(encoding="utf-8").splitlines()
            if handle in content:
                content.remove(handle)
                with file.open(mode="w", encoding="utf-8", newline="\n") as f:
                    f.write('\n'.join(content))
                print(f'{handle} was removed from {file.stem}')
                found_handle = True

        if not found_handle:
            print(f'The handle {handle} was not found inside any file')

    def get_df_to_iterate(self, playlist_folder: Path, YT_content_creators: pd.DataFrame) -> pd.DataFrame:
        if not playlist_folder.exists():
            print('There is not a playlist folder')
            return
        search_options = ['Complete DataFrame', 
                          'Podcast or Playlist from a Channel',
                          'Only some Playlist in the iteration',
                          'Remove Playlist from the iteration',
                          'Only search for some Handles',
                          'Exit Process']
        search_handles = choose_option(search_options, 'Search for a Particular Handles')
        
        if search_handles == search_options[0]:
            YT_content_creators_iter = YT_content_creators
            
        elif search_handles == search_options[1]:
            YT_content_creators_iter = YT_content_creators[YT_content_creators['uploads'].str.startswith('PL')].reset_index(drop=True)
            
        elif search_handles == search_options[2] or search_handles == search_options[3]:
            if search_handles == search_options[2]:
                message = 'Handles from Playlist to be include in the Data Frame'
                message_2 = "Playlist that would be in the Data Frame"
            else:
                message = 'Handles from Playlist that would not be include in the iteration of the Data Frame'
                message_2 = 'Playlist that would not be in the Data Frame'
            playlist_chosen = []
            youtube_names_iter = [file.stem.replace("_", " ").strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
            playlist_to_search = choose_option(youtube_names_iter, message)
            playlist_chosen.append(playlist_to_search)
            file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
            handles_filter = self.files_manager.get_elements_from_file(file_path, False)
            youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
            while True:
                continue_adding = choose_option([True, False], "Add more Playlist into the filter:")
                if continue_adding:
                    playlist_to_search = choose_option(youtube_names_iter, 'Paylist to search new Handles')
                    youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
                    file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
                    handles_filter.extend(self.files_manager.get_elements_from_file(file_path, False))
                    playlist_chosen.append(playlist_to_search)
                else:
                    break
            print(f'{message_2}: {", ".join(playlist_chosen)}')
            if search_handles == search_options[2]:
                YT_content_creators_iter = YT_content_creators[YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)
            if search_handles == search_options[3]:
                YT_content_creators_iter = YT_content_creators[~YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)                

        elif search_handles == search_options[4]:
            handles_filter = []
            while True:
                handles_to_search = input('New videos in the Handle: ').strip().lower()
                handles_filter.append(handles_to_search)
                if not choose_option([True, False], "Add Handles into the new DataFrame:"):
                    print(f'Handles to be include in the DataFrame: {", ".join(sorted(handles_filter))}')
                    break
            YT_content_creators_iter = YT_content_creators[YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)
        elif search_handles == search_options[5]:
            return None
        
        return YT_content_creators_iter

if __name__ == "__main__":
    test = df_manager()
    fm = filesManager()
    df = fm.YT_content_creators
    df = test.get_df_to_iterate(playlist_folder, df)
    print(df)
