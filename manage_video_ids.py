from pathlib import Path
from urllib.parse import urlparse, parse_qs
from app_functions import (choose_option, 
                           search_string_folder,
                           remove_accents)
from paths import (content_creator_folder,
                   exception_folder,
                   yt_channel)

from filesManager import filesManager
from YouTube import YouTubeManager
from response import response_manager
from df_manager import df_manager
import pandas as pd
fm = filesManager()
yt = YouTubeManager()
res_mng = response_manager()

def get_video_id(url: str | None = None) -> str:
    if not url:
        url = input("Video ID or URL: ").strip()
    url = url.strip().replace('shorts/', 'watch?v=')
    if 'https://www.youtube.com/watch?v=' not in url:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("v", [url])[0]  # default to 0 if missing

def get_playlist_id(url: str) -> str:

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("list", [url])[0]  # default to 0 if missing

def add_video_manually(url: str) -> None:
    if url is None:
        video_id = get_video_id(input('Video ID to add a file: '))
    else:
        video_id = get_video_id(url.strip())
        if video_id == 0:
            print(f'{url} is not a valid url or video id')
            return
    if search_string_folder(content_creator_folder, video_id):
        return
    response = yt.get_response_video_id(video_id) # type: ignore
    
    video_info = res_mng.get_video_info(response, False, True)
    if not video_info:
        print(f'Video ID {video_id} does not have any information')
        return
    

    channelId = video_info['channelId']
    response_channel = yt.get_channel_response(channelId)
    if not response_channel:
        print(f'There was not possible to get the Response of the channel of the Video ID: {video_id}')
        return
    channel_info =  res_mng.get_channel_info(response_channel)
    if channel_info is None:
        print(f'There was not possible to get a response for the channel of {yt_channel}{channelId}')
        return
    handle = channel_info['customUrl']
    handle_file_path = content_creator_folder / f'{handle}.txt'

    if handle_file_path.exists():
        res_mng.get_video_info(response, True, True)
        print('*'*75)
        fm.add_element_to_file(handle_file_path, video_id, True, True)
    else:        
        print(f'The file handle {handle_file_path.stem} does not exists')

def manage_exceptions() -> None:
    files_dict = {file.stem: file for file in exception_folder.rglob('*') if file.suffix == '.txt' or file.suffix == '.json'}
    
    options = list(files_dict.keys())
    options.append('New Exception File in Txt')
    option_choosen = choose_option(options, message="Choose the Exception to add: ")
    handles_df = df_manager().handles_df
    if option_choosen is None:
        print('There was an error choosing the file')
        return
    elif option_choosen == options[-1]:
        print('Creating a new file')
    else:
        file_path = files_dict[option_choosen]
        handle = input('Handle: ').strip().lower()
        if handle not in handles_df:
            print(f'The handles {handle} is not in the DataFrame and is not going to be added to any excption')
        elif file_path.suffix.lower() == '.txt':
            fm.add_element_to_file(file_path, handle, True, True)
        else:
            key = input(f'The value to add in the file {file_path.name} to the handle {handle}: ').strip().lower()
            handle_dict = fm.read_json(file_path, False)
            if handle in handle_dict and key not in handle_dict[handle]:
                handle_dict[handle].append(key)
            else:
                handle_dict[handle] = [key]
            fm.write_json(handle_dict, file_path)


        



if __name__ == "__main__":
    manage_exceptions()