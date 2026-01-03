from pathlib import Path
from IPython.display import clear_output  # optional, can remove later



def add_video_manually(YouTubeManager, filesManager, response_mnr, video_id, verbose=True):
    video_id = video_id.strip()
    # response = YouTubeManager.get_response_video_id(YouTubeManager.youtube, filesManager.quota_filename, video_id)
    response = YouTubeManager.get_response_video_id(video_id)
    channelId = response['items'][0]['snippet']['channelId']
    # response_channel = YouTubeManager.get_channel_response(YouTubeManager.youtube, filesManager.quota_filename, channelId)
    response_channel = YouTubeManager.get_channel_response(channelId)
    handle = response_channel['items'][0]['snippet']['customUrl'].replace('@', '')
    handle_file_path = filesManager.content_creator_folder / f'{handle}.txt'
    if handle_file_path.exists():
        print(handle_file_path)
        filesManager.add_element_to_file(handle_file_path, video_id, True, True)
    else:
        clear_output(wait=False)
        print('The file handle does not exists')


# video_id = get_video_id(input('Add a video ID manually: ').strip())
# print(yt_url + video_id)
# response = get_response_video_id(youtube, quota_filename, video_id)
# metadata_video = get_metadata_video(response)
# channelId = response['items'][0]['snippet']['channelId']
# response_channel = get_channel_response(youtube, quota_filename, channelId)
# handle = response_channel['items'][0]['snippet']['customUrl'].replace('@', '')
# print(f'The YouTube handle is: {handle}')
# print(f'https://www.youtube.com/channel/{channelId}')
# for info in metadata_video:
#     print(info)
# handle_file_path = Content_Creator_folder / f'{handle}.txt'

# if handle_file_path.exists():
#     print(handle_file_path)
#     add_element_to_file(handle_file_path, video_id, True, True)
# else:
#     clear_output(wait=False)
#     print('Not Added')