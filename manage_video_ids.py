from pathlib import Path
from urllib.parse import urlparse, parse_qs
from app_functions import (choose_option, 
                           search_string_folder,
                           duration_string)
from paths import (content_creator_folder,
                   exception_folder)

from filesManager import filesManager

fm = filesManager()

def get_video_id(url: str) -> str:
    url = url.strip().replace('shorts/', 'watch?v=')
    if 'https://www.youtube.com/watch?v=' not in url:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("v", [0])[0]  # default to 0 if missing

def get_playlist_id(url: str) -> str:

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("list", [url])[0]  # default to 0 if missing

def add_video_manually(YouTubeManager: classmethod, response_manager: classmethod, filesManager: classmethod, url: str) -> None:
    if url is None:
        video_id = get_video_id(input('Video ID to add a file: '))
    else:
        video_id = get_video_id(url.strip())
        if video_id == 0:
            print(f'{url} is not a valid url or video id')
            return
    if search_string_folder(content_creator_folder, video_id):
        return
    response = YouTubeManager.get_response_video_id(video_id)
    
    video_info = response_manager.get_video_info(response, False, True)
    if not video_info:
        print(f'Video ID {video_id} does not have any information')
        return
    

    channelId = video_info['channelId']
    response_channel = YouTubeManager.get_channel_response(channelId)
    channel_info =  response_manager.get_channel_info(response_channel)
    handle = channel_info['customUrl']
    
    handle_file_path = content_creator_folder / f'{handle}.txt'

    for k in list(video_info.keys()):
        if not video_info[k] or video_info[k] == 'none':
            del video_info[k]

    if handle_file_path.exists():
        response_manager.get_video_info(response, True, True)
        print('*'*75)
        filesManager.add_element_to_file(handle_file_path, video_id, True, True)
    else:
        
        print(f'The file handle {handle_file_path.stem} does not exists')

def manage_exceptions(filesManager: classmethod) -> None:
    options = [file for file in exception_folder.iterdir() if file.suffix == '.txt' or file.suffix == '.json']
    options.append('New Exception File')
    exception_file = choose_option(options, message="Choose the Exception to add: ")
    if exception_file == options[-1]:
        new_file_name = input('New file:').strip()
        exception_file = exception_folder / new_file_name
        exception_element = input(f'Video ID of a Vertical Video ID: ')

    elif exception_file.suffix == '.json':
        dictionary = fm.read_json(exception_file)
        handle = input("Handle: ").strip().lower()
        key = input(f"Word in title from the handle: {handle}: ").strip().lower()
        if handle in dictionary and key not in dictionary[handle]:
            print('The Handle Exists')
            dictionary[handle].append(key)
        else:
            dictionary[handle] = [key]
        fm.write_json(dictionary, exception_file)
        return 
    
    else:
        exception_element = input(f'Handle or Title to Add in {exception_file.stem}: ').lower()
    filesManager.add_element_to_file(exception_file, exception_element, sort_list=True, print_statement=True)
    print(exception_file)



if __name__ == "__main__":
    pass