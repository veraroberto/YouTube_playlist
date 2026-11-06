from filesManager import filesManager
from YouTube import YouTubeManager
from response import response_manager


from app_functions import (choose_option,
                           remove_accents,
                           get_videoId,
                           get_playlist_id)

from paths import (playlist_folder,
                   exception_folder,
                   content_creator_folder,
                   yt_url,
                   DATA_DIR)
# from manage_videoIds import manage_exceptions
from typing import cast
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
        if 'customUrl' in columns_df:
            self.customUrls_df = self.YT_content_creators['customUrl'].values
        else:
            self.customUrls_df = []

        self.playlist_files = [file for file in playlist_folder.iterdir() if file.suffix == '.txt']
        self.playlist_names = [playlist.stem.replace('_', ' ').strip() for playlist in self.playlist_files]

        self.yt = YouTubeManager()
        self.response_mgr = response_manager()

    def update_df(self,
                  df_path: None | Path = None,
                  new_row: dict | list[dict] | None = None,
                  columns_df: list = columns_df,
                  sort_by: str = ""
                  ) -> None:
        if new_row is None:
            print('There is nothing to update')
            return
        
        if df_path is None:
            df_path = self.file_path_yt_creators

        if not df_path.exists():
            cols = columns_df if columns_df is not None else columns_df
            df = pd.DataFrame(columns=cols)
        else:
            df = pd.read_csv(df_path)

        if isinstance(new_row, dict):
            new_row = [new_row]

        if new_row:
            new_df = pd.DataFrame(new_row)
            df = pd.concat([df, new_df], ignore_index=True)
            if sort_by and sort_by in df.columns:
                df = df.sort_values(by=sort_by)
            self.files_manager.write_csv_safely(df, df_path)
        
        
    def add_row_df(self) -> None:
        options = ['Video ID',
                   'customUrl',
                   'Channel ID',
                   'Playlist ID']
        chosen = choose_option(options, "Add row by")

        if chosen == None:
            return
        elif chosen == options[0]: # Video ID
            videoId = get_videoId(input("Video ID or the URL of the channel: ").strip())
            response = self.yt.get_response_videoId(videoId)
            if response is None:
                print(f"There is not response for video ID: {videoId}")
                return
            video_info = self.response_mgr.get_video_info(response)
            if video_info is None:
                print(f'There is no response to the video ID {yt_url}{videoId}')
                return
            channelId = video_info['channelId']
            channel_response = self.yt.get_channel_response(channelId)
            if channel_response is None:
                print("Not adding a new row")
                return
            info_df = self.response_mgr.get_channel_info(channel_response)                
        elif chosen == options[1]: # customUrl
            print('By customUrls')
            customUrl = remove_accents(input("New customUrl: ").replace('@', "").lower().strip())
            if customUrl in self.YT_content_creators['customUrl'].values:
                print(f'customUrl {customUrl} is already in the DataFrame')
                return
            else:
                print(f'{customUrl} is going to be added to the Data Frame')
                channel_response = self.yt.get_response_channel_by_customUrl(customUrl)
                if channel_response is None:
                    return
                info_df = self.response_mgr.get_channel_info(channel_response)
        elif chosen == options[2]: # Channel ID
            channelId = input('Add a new Row by channelId: ')
            if channelId in self.YT_content_creators['channelId'].values:
                print(f"The channelId {channelId} is already in the Data Frame")
                return
            else:
                channel_response = self.yt.get_channel_response(channelId)
                if channel_response is None:
                    print("There is not going to be added a new row")
                    return
                info_df = self.response_mgr.get_channel_info(channel_response) 
        elif chosen == options[3]: # Playlist 
            playlist_id =  get_playlist_id(input('Get the new playlist ID: ').strip())
            if playlist_id in self.YT_content_creators['uploads'].values:
                print(f'The Playlist {playlist_id} ID is already in the DF')
                return
            else:
                playlist_response = self.yt.get_response_from_playlist_id(playlist_id)
                if playlist_response is None:
                    print(f'There is no response for the playlist {playlist_id}')
                    return
                info_df = self.response_mgr.get_playlist_info(playlist_response, True)
        else:
            return
        if info_df is None:
            print(f'There was no info to add to the new row ')
            return
            
        customUrl = remove_accents(info_df['customUrl'])
        channelTitle = info_df['channelTitle']
        channelId = info_df['channelId']
        uploads = info_df['uploads']   

        #Sort the new row into a Playlist
        self.playlist_names.extend(['Other Videos', "New Playlist"])
        customUrl_playlist = choose_option(self.playlist_names, f"Add the new {chosen} to the Playlist:")
        if customUrl_playlist is None:
            print('There is not a customUrl selected')
            return
        if customUrl_playlist == self.playlist_names[-2]:
            print(f'{chosen} is not going to be added to any particular playlist')
        elif customUrl_playlist == self.playlist_names[-1]:
            new_playlist_name = input('Name of the New Playlist: ').strip()
            playlist_file_path = playlist_folder / f'{new_playlist_name.replace(" ", "_")}.txt'
            if playlist_file_path.exists():
                print(f'The new Playlist: {new_playlist_name} is already in the files.')
            else:
                  self.files_manager.add_element_to_file(playlist_file_path,
                                                         customUrl, 
                                                         sort_list=True,
                                                         print_statement=False,
                                                         create_file=True)
        else:
            customUrl_playlist = cast(str, customUrl_playlist)
            playlist_file_path = playlist_folder / f'{customUrl_playlist.replace(" ","_")}.txt'
            self.files_manager.add_element_to_file(playlist_file_path, customUrl, sort_list=True)
        item_resposnes = self.yt.get_all_ids_playlist(uploads, 200)
        videoIds_yt = [item.get('videoId') for item in item_resposnes]
        if videoIds_yt:    
        # print(f'Time getting the video ids: {duration_string(time.time() - inicio)}')

            #Add the Videos IDs of the new row to the txt files
            file_path_videoIds = content_creator_folder / f'{customUrl}.txt'
            print(f'{customUrl} has {len(videoIds_yt):,} videos')
            elements_videoIds = videoIds_yt[1:]
            self.files_manager.add_list_to_file(file_path_videoIds, elements_videoIds, sort_list=False, create_file=True)

        # Adding the new row
        new_row = customUrl, channelTitle, channelId, uploads
        self.YT_content_creators.loc[len(self.YT_content_creators)] = new_row
        self.YT_content_creators.sort_values(by='customUrl', inplace = True,  key=lambda col: col.str.lower())
        self.YT_content_creators.reset_index(drop=True, inplace=True)
        self.files_manager.write_csv_safely(self.YT_content_creators, self.file_path_yt_creators)
        
        if choose_option([True, False], "Add an exception: "):
            exception_files = [file.stem for file in exception_folder.iterdir() if file.suffix =='.txt']
            print(exception_files)
            while True:
                file = choose_option(exception_files, "Choose the to Exception file to add the customUrl")
                if file is None:
                    print('No file was selected')
                    return
                file_path = exception_folder / f'{file}.txt'
                self.files_manager.add_element_to_file(file_path, customUrl, sort_list=True, print_statement=False)
                
                if not choose_option([True, False], "Continue Adding Exception: "):
                    break
                exception_files.remove(cast(str,file))

    def delete_information_in_files(self) -> None:
        # customUrl = remove_accents(input('Select a customUrl to delete: ').strip().lower().replace(" ","_"))
        customUrl = input('Select a customUrl to delete: ').strip().lower().replace(" ","_")

        
        # Folders
        # content_creator_folder = self.files_manager.content_creator_folder
        if customUrl not in self.YT_content_creators['customUrl'].values:
            print(f'The customUrl {customUrl} is not in the DF')
            # return
        else:
            self.YT_content_creators = self.YT_content_creators[self.YT_content_creators['customUrl'] != customUrl]
            self.YT_content_creators.sort_values(by='customUrl', inplace = True,  key=lambda col: col.str.lower())
            self.YT_content_creators.reset_index(drop=True, inplace=True)
            self.files_manager.write_csv_safely(self.YT_content_creators, self.file_path_yt_creators)
            print(f'{customUrl} was removed from the Data Frame')
        
        for file_customUrl in DATA_DIR.rglob('*'):
            if file_customUrl.stem == customUrl:
                try:
                    file_customUrl.unlink()
                    print(f'The file {file_customUrl.name} was deleted')
                except Exception as e:
                    print(f'The file {file_customUrl.name} does not exists. The error is {e}')

        # Remove customUrl from all the txt files
        search_folder = [
            playlist_folder,
            exception_folder,
       ]
        for folder in search_folder:
            self.files_manager.delete_string_from_txt_files(folder, customUrl)
 

    def get_df_to_iterate(self, playlist_folder: Path, YT_content_creators: pd.DataFrame) -> pd.DataFrame | None:
        if not playlist_folder.exists():
            print('There is not a playlist folder')
            return
        search_options = ['Complete DataFrame', 
                          'Podcast or Playlist from a Channel',
                          'Only some Playlist in the iteration',
                          'Remove Playlist from the iteration',
                          'Only search for some customUrls',
                          'Add to files the videos that were manually added to the Playlists',
                          'Exit Process']
        search_customUrls = choose_option(search_options, 'Search for a Particular customUrls')

        if search_customUrls == search_options[0]:
            YT_content_creators_iter = YT_content_creators
            
        elif search_customUrls == search_options[1]:
            YT_content_creators_iter = YT_content_creators[YT_content_creators['uploads'].str.startswith('PL')].reset_index(drop=True)
            
        elif search_customUrls == search_options[2] or search_customUrls == search_options[3]:
            if search_customUrls == search_options[2]:
                message = 'customUrls from Playlist to be include in the Data Frame'
                message_2 = "Playlist that would be in the Data Frame"
            else:
                message = 'customUrls from Playlist that would not be include in the iteration of the Data Frame'
                message_2 = 'Playlist that would not be in the Data Frame'
            playlist_chosen = []
            youtube_names_iter = [file.stem.replace("_", " ").strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
            youtube_names_iter.sort()
            playlist_to_search = choose_option(youtube_names_iter, message)
            if not playlist_to_search or isinstance(playlist_to_search, dict):
                print("The is no DF to iterate")
                return
            playlist_chosen.append(playlist_to_search)
            file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
            customUrls_filter = self.files_manager.get_elements_from_file(file_path, False)
            youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
            while True:
                continue_adding = choose_option([True, False], "Add more Playlist into the filter:")
                if continue_adding is None:
                    print('A problem in the Filter')
                    return
                if continue_adding:
                    playlist_to_search = choose_option(youtube_names_iter, 'Playlist to search new customUrls')
                    if playlist_to_search is None:
                        print('No Playlist')
                        return
                    playlist_to_search = cast(str, playlist_to_search)
                    youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
                    file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
                    customUrls_filter.extend(self.files_manager.get_elements_from_file(file_path, False))
                    playlist_chosen.append(playlist_to_search)
                else:
                    break
            print(f'{message_2}: {", ".join(playlist_chosen)}')
            if search_customUrls == search_options[2]:
                YT_content_creators_iter = YT_content_creators[YT_content_creators['customUrl'].isin(customUrls_filter)].reset_index(drop=True)
            else:
                YT_content_creators_iter = YT_content_creators[~YT_content_creators['customUrl'].isin(customUrls_filter)].reset_index(drop=True)                

        elif search_customUrls == search_options[4]:
            customUrls_filter = []
            while True:
                customUrls_to_search = input('New videos in the customUrl: ').strip().lower()
                customUrls_filter.append(customUrls_to_search)
                if not choose_option([True, False], "Add customUrls into the new DataFrame:"):
                    print(f'customUrls to be include in the DataFrame: {", ".join(sorted(customUrls_filter))}')
                    break
            YT_content_creators_iter = YT_content_creators[YT_content_creators['customUrl'].isin(customUrls_filter)].reset_index(drop=True)
        elif search_customUrls == search_options[5]: # Retrun an empty DataFrame
            YT_content_creators_iter = YT_content_creators.head(0)
            
        else:
            print(f'In function. Not maing. Doing nothing')
            return None
        
        return YT_content_creators_iter
    
if __name__ == "__main__":
    
    pass
