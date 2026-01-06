from pathlib import Path
from IPython.display import clear_output  # optional, can remove later



def add_video_manually(YouTubeManager, filesManager, video_id):
    if video_id is None:
        video_id = input('Video ID to add a file: ')
    video_id = video_id.strip()
    response = YouTubeManager.get_response_video_id(video_id)
    items = response.get('items', [])
    if not items:
        print(f'Video ID {video_id} does not have any information')
        return
    
    channelId = items[0]['snippet']['channelId']
    response_channel = YouTubeManager.get_channel_response(channelId)
    handle = response_channel['items'][0]['snippet']['customUrl'].replace('@', '')
    handle_file_path = filesManager.content_creator_folder / f'{handle}.txt'
    if handle_file_path.exists():
        print(handle_file_path)
        filesManager.add_element_to_file(handle_file_path, video_id, True, True)
    else:
        clear_output(wait=False)
        print('The file handle does not exists')

def manage_exceptions(filesManager, app):
    options = [file for file in filesManager.exception_folder.iterdir() if file.suffix == '.txt']
    options.append('New Exception File')
    exception_file = app.choose_option(options, message="Choose the Exception to add: ")
    if exception_file == options[-1]:
        new_file_name = input('New file:').strip()
        exception_file = filesManager.exception_folder / new_file_name
        exception_element = input(f'Video ID of a Vertical Video ID: ')
        
    else:
        exception_element = input(f'Handle or Title to Add in {exception_file.stem}: ').lower()
    filesManager.add_element_to_file(exception_file, exception_element, sort_list=True, print_statement=True)
    print(exception_file)



if __name__ == "__main__":
    from filesManager import filesManager
    from app import app
    fm = filesManager()
    fncs = app()

    manage_exceptions(fm, fncs)