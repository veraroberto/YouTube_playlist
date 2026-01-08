from filesManager import filesManager
from YouTube import YouTubeManager


from app_functions import choose_option, remove_accents

from pathlib import Path
import pandas as pd

class df_manager:
    columns = ['Handle', 'channelName', 'channelID', 'uploadsID']
    def __init__(self):
        self.files_manager = filesManager()
        self.yt = YouTubeManager()
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
                   'Playlist ID']
        chosen = choose_option(options, "Add row by")

        if chosen == options[0]: # Video ID
            # Need to get the handle
            pass
        elif chosen == options[1]: #Handle
            handle = remove_accents(input("New Handle: ").replace('@', "").lower().strip())
            if handle in self.YT_content_creators['Handle'].values:
                print(f'Handle {handle} is already in the DataFrame')
                return
            else:
                print(f'{handle} is going to be added to the Data Frame')
            


        elif chosen == options[2]:
            # The handle is going to be the Playlist name with "_"
            pass
        #Sort the new row into a Playlist
        # playlists_info = self.yt.get_all_playlists()
        self.playlist_names.extend(['Other Videos', "New Playlist"])

        handle_playlist = choose_option(self.playlist_names, f"Add the new {chosen} to the Playlist:")
        if handle_playlist == self.playlist_names[-2]:
            print(f'{chosen} is not going to be added to any particular playlist')
        if handle_playlist == self.playlist_names[-1]:
            new_playlist_name = input('Name of the New Playlist: ').strip()
            playlist_file_path = self.files_manager.playlist_folder / f'{handle_playlist}.txt'
            if playlist_file_path.exists():
                print(f'The new Playlist: {new_playlist_name} is already in the files.')
            else:
                
                self.files_manager.add_element_to_file(playlist_file_path, handle, sort_list=True, print_statement=False)
            # playlist_exist = next((d["name"] for d in playlists_info if new_playlist_name in d.values()), None)
            # if playlist_exist is None:
            #     print(f'{new_playlist_name} is going to be created')


                # # playlist_id = next((d["id"] for d in playlists_info if handle_playlist in d.values()), None)
                # print(f'Playlist Name: {handle_playlist}')
                # print(f'Playlist ID: {playlist_id}')
            

    





if __name__ == "__main__":
    test = df_manager()
    test.add_row_df()
    
