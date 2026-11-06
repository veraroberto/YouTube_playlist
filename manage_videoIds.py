from pathlib import Path
from urllib.parse import urlparse, parse_qs
from app_functions import (choose_option, 
                           search_string_folder,
                           remove_accents,
                           clear_terminal)
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

YT_df = fm.YT_content_creators

def get_videoId(url: str | None = None) -> str:
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

def add_video_manually(url: str, print_statement: bool = False) -> dict | None:
    if url is None:
        videoId = get_videoId(input('Video ID to add a file: '))
    else:
        videoId = get_videoId(url.strip())
        if videoId == 0:
            print(f'{url} is not a valid url or video id')
            return 
    if search_string_folder(content_creator_folder, videoId):
        return 
    response = yt.get_response_videoId(videoId) 
    
    video_info = res_mng.get_video_info(response, False, True)
    if not video_info:
        print(f'Video ID {videoId} does not have any information')
        return 
    
    channelId = video_info['channelId']
    if channelId in YT_df['channelId'].values:
        customUrl = YT_df.loc[YT_df['channelId'] == channelId, 'customUrl'].values[0]
        customUrl_file_path = content_creator_folder / f'{customUrl}.txt'

    else:
        response_channel = yt.get_channel_response(channelId)
        if not response_channel:
            print(f'There was not possible to get the Response of the channel of the Video ID: {videoId}')
            return 
        channel_info =  res_mng.get_channel_info(response_channel)
        if channel_info is None:
            print(f'There was not possible to get a response for the channel of {yt_channel}{channelId}')
            return 
        customUrl = channel_info['customUrl']
        customUrl_file_path = content_creator_folder / f'{customUrl}.txt'

    if customUrl_file_path.exists():
        fm.add_element_to_file(customUrl_file_path, videoId, sort_list=False, print_statement=False, create_file = False)
        res_mng.get_video_info(response, print_info=True, del_extra_keys=True)
        print("*"*100)
    else:
        if print_statement: 
            print(f'The file customUrl {customUrl_file_path.stem} does not exists')
        return 

    return video_info

def manage_exceptions() -> None:
    files_dict = {file.stem: file for file in exception_folder.rglob('*') if file.suffix == '.txt' or file.suffix == '.json'}
    
    options = list(files_dict.keys())
    options.append('New Exception File in Txt')
    option_choosen = choose_option(options, message="Choose the Exception to add: ")
    customUrls_df = df_manager().customUrls_df
    if option_choosen is None:
        print('There was an error choosing the file')
        return
    elif option_choosen == options[-1]:
        print('Creating a new file')
    else:
        file_path = files_dict[option_choosen]
        while True:
            customUrl = input(f'New customUrl in {file_path.stem}: ').strip().lower()
            if customUrl not in customUrls_df:
                print(f'The customUrls {customUrl} is not in the DataFrame and is not going to be added to any excption')
            elif file_path.suffix.lower() == '.txt':
                fm.add_element_to_file(file_path, customUrl, True, True)
            else:
                key = input(f'The value to add in the file {file_path.name} to the customUrl {customUrl}: ').strip().lower()
                customUrl_dict = fm.read_json(file_path, False)
                if customUrl in customUrl_dict and key not in customUrl_dict[customUrl]:
                    customUrl_dict[customUrl].append(key)
                else:
                    customUrl_dict[customUrl] = [key]
                fm.write_json(customUrl_dict, file_path)
            if not choose_option([True, False], f'Add a new customUrl to {file_path.stem}'):
                break
            clear_terminal()
            


        



if __name__ == "__main__":
    manage_exceptions()
  