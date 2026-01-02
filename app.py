from filesManager import filesManager

import pyperclip, string, itertools, unicodedata, requests
import pandas as pd
from IPython.display import clear_output

class app():
    def __init__(self,):
        self.files_manager = filesManager()

    def choose_option(self, options, message="Enter your choice: "):
        pyperclip.copy('')
        
        # 1. Generate Excel-style labels (a, b... z, aa, ab...)
        def get_labels(count):
            labels = []
            n = 1
            while len(labels) < count:
                # Generate combinations of length n ('a', then 'aa', then 'aaa')
                for combo in itertools.product(string.ascii_uppercase, repeat=n):
                    labels.append("".join(combo))
                    if len(labels) == count:
                        break
                n += 1
            return labels
    
        # 2. Map labels to options
        option_labels = get_labels(len(options))
        option_map = dict(zip(option_labels, options))
    
        while True:
            print(message)
            for letter, option in option_map.items():
                print(f"  {letter}) {option}")
            choice = input("Enter your choice: ").strip().upper()
            # Check for user input or the pyperclip bypass
            if choice in option_map or pyperclip.paste() == 'choose_option':
                if pyperclip.paste() == 'choose_option':
                    print('There was no option chosen and the function was interrupted')
                    return None
                
                print(f"  {choice}) {option_map[choice]}")
                return option_map[choice]
            else:
                print("Invalid choice. Please try again.\n")

    def get_df_to_iterate(self, playlist_folder, YT_content_creators):
        if not playlist_folder.exists():
            print('There is not a playlist folder')
            return
        search_options = ['Complete DataFrame', 
                          'Podcast or Playlist from a Channel',
                          'Only some Playlist in the iteration',
                          'Remove Playlist from the iteration',
                          'Only search for some Handles']
        search_handles = self.choose_option(search_options, 'Search for a Particular Handles')
        
        if search_handles == search_options[0]:
            YT_content_creators_iter = YT_content_creators
            clear_output(wait=False)
        elif search_handles == search_options[1]:
            YT_content_creators_iter = YT_content_creators[YT_content_creators['uploadsID'].str.startswith('PL')].reset_index(drop=True)
            clear_output(wait=False)
        elif search_handles == search_options[2] or search_handles == search_options[3]:
            clear_output(wait=False)
            if search_handles == search_options[2]:
                message = 'Handles from Playlist to be incluede in the Data Frame'
                message_2 = "Playlist that would be in the Data Frame"
            else:
                message = 'Handles from Playlist that would not be incluede in the iteration of the Data Frame'
                message_2 = 'Playlist that would not be in the Data Frame'
            playlist_choosen = []
            youtube_names_iter = [file.stem.replace("_", " ").strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
            playlist_to_search = self.choose_option(youtube_names_iter, message)
            playlist_choosen.append(playlist_to_search)
            file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
            handles_filter = self.files_manager.get_elements_from_file(file_path, False)
            youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
            while True:
                continue_adding = self.choose_option([True, False], "Add more Playlist into the filter:")
                if continue_adding:
                    clear_output(wait=False) 
                    playlist_to_search = self.choose_option(youtube_names_iter, 'Paylist to search new Handles')
                    youtube_names_iter.pop(youtube_names_iter.index(playlist_to_search))
                    file_path = playlist_folder / f'{playlist_to_search.replace(" ", "_")}.txt'
                    handles_filter.extend(self.files_manager.get_elements_from_file(file_path, False))
                    playlist_choosen.append(playlist_to_search)
                else:
                    break
            clear_output(wait=False)
            print(f'{message_2}: {", ".join(playlist_choosen)}')
            if search_handles == search_options[2]:
                YT_content_creators_iter = YT_content_creators[YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)
            if search_handles == search_options[3]:
                YT_content_creators_iter = YT_content_creators[~YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)                

        elif search_handles == search_options[4]:
            clear_output(wait=False)
            handles_filter = []
            while True:
                if self.choose_option([True, False], "Add Handles into the new DataFrame:"):
                    clear_output(wait=False)
                    handles_to_search = input('New video in Handle: ').strip().lower()
                    handles_filter.append(handles_to_search)
                    print(f'Handles to be include in the DataFrame: {", ".join(handles_filter)}')
                else:
                    clear_output(wait=False)
                    print(f'Handles to be include in the DataFrame: {", ".join(handles_filter)}')
                    break
            YT_content_creators_iter = YT_content_creators[YT_content_creators['Handle'].isin(handles_filter)].reset_index(drop=True)
        return YT_content_creators_iter

    def duration_string(self,duration):
        #Duration in seconds
        if isinstance(duration, (float, int)):
            hrs, mins = divmod(duration, 3600)
            mins, secs = divmod(mins, 60)
            duration_string = f'{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}'
            return duration_string
        else:
            print(f'{duration} is not a number')
    def remove_accents(self, text: str) -> str:
        # Normalize the text to separate base letters and diacritics
        normalized = unicodedata.normalize('NFD', text)
        # Filter out the diacritic marks
        without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return without_accents

    def is_short(self, video_id):
        url = f'https://www.youtube.com/shorts/{video_id}'
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 429:
            print("Too many requests — you've hit a rate limit.")
            return 
        elif response.status_code == 403:
            print("Access forbidden — you may be blocked.")
            return 
        
        # The final URL after redirects
        final_url = response.url
    
        # If it redirects to the watch URL, it's not a Short
        if 'youtube.com/watch?v=' in final_url:
            return False
        elif 'youtube.com/shorts/' in final_url:
            return True
        else:
            return  # Unexpected case
    