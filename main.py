import argparse
from YouTube import YouTubeManager
from filesManager import filesManager
from app import app
from response import response_manager
from manage_video_ids import add_video_manually, manage_exceptions


# from itertools import count
from pathlib import Path
from collections import defaultdict

# import pandas as pd

import time, re, pyperclip

from app_functions import choose_option

def main():

    add_video_to_playlist = True
    parser = argparse.ArgumentParser(
        description="YouTube Playlist Organizer"
    )

 
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("quota", help="Show today's consumed YouTube API quota")

    add_parser = subparsers.add_parser("add-video", help="Manually add a video by ID to the files")
    add_parser.add_argument("--video_id", required=False, help="YouTube video ID to add (if not provided, you'll be prompted)")

    add_parser = subparsers.add_parser("add-list-videos", help="Manually add a list of video by ID to the files")
    add_parser.add_argument("--video_id", required=False, help="Copies the URL from the clipboard")

    subparsers.add_parser("add-exception", help="Add an exception to a file")
    
    add_parser = subparsers.add_parser("not-add-videos", help="Do not add the Video to the Playlists")
    # add_parser.add_argument("--video_id", required=False, help="Copies the URL from the clipboard")

    args = parser.parse_args()

    files_manager = filesManager()
    yt = YouTubeManager()
    functions = app()
    response_mnr = response_manager()


    if args.command == 'quota':
        files_manager = filesManager()
        files_manager.get_today_quota(True)
        return

    elif args.command == "add-video":
        while True:
            add_video_manually(yt, 
                            files_manager, 
                            url=args.video_id, 
                            )
            if not choose_option([True, False], message="Add another video ID: "):
                break
        return
    
    elif args.command == 'add-list-videos':
        input('Click enter when the list of links is in the clipboard ')
        links_list = pyperclip.paste().splitlines()
        for video_id in links_list:
            add_video_manually(yt,
                               files_manager,
                               url=video_id
                               )
        return

    elif args.command == "add-exception":
        manage_exceptions(files_manager, functions)
        return  

    elif args.command == "not-add-videos":
        add_video_to_playlist = False
        print("No video will be added to the Playlist")


    YT_content_creators_iter = functions.get_df_to_iterate(files_manager.playlist_folder, files_manager.YT_content_creators)
    if YT_content_creators_iter is None:
        print("Doing Nothing")
        return
    # yt_channel = 'https://www.youtube.com/channel/'
    yt_url = 'https://www.youtube.com/watch?v='

    ## Creates the Dictionary of the Playlists
    playlist_names = yt.get_all_playlists()
    youtube_names = [file.stem.replace('_', ' ').strip() for file in files_manager.playlist_folder.iterdir() if file.suffix == '.txt']
    youtube_playlists = defaultdict(lambda:
                                    {"Handles":[],
                                    "Playlist_ID": "",
                                    "video_ids": [],
                                    "new_video_ids": [],
                                    }
                                    )

    shorts_playlist_name = 'Shorts To Watch'
    other_playlist_name = 'Videos To Watch'
    WL_shorts_playlist = 'Watch Later Shorts'
    vertical_video_id = files_manager.get_elements_from_file(files_manager.exception_folder / "vertical_video.txt", create_file=False)
    special_playlist = [other_playlist_name, WL_shorts_playlist, shorts_playlist_name]
    # youtube_names.extend({'Path': None, 'Name': playlist} for playlist in special_playlist)
    youtube_names.extend(special_playlist)

    for playlist in youtube_names:
        file_path = files_manager.playlist_folder / f'{playlist.replace(" ","_")}.txt'
        if file_path.exists():
            handles = file_path.read_text(encoding="utf-8").splitlines()
            youtube_playlists[playlist]['Handles'].extend(handles) 

        #Getting the Playlist ID
        playlist_id = next((d["id"] for d in playlist_names if playlist in d.values()), None)
        youtube_playlists[playlist]['Playlist_ID'] = playlist_id

        if playlist_id:
            video_ids = yt.get_all_ids_playlist(playlist_id, 300)
            youtube_playlists[playlist]['video_ids'].extend(video_ids)

    all_ids_from_playlist = [video_id for playlist in youtube_playlists.values() for video_id in playlist['video_ids']]
    print(f'There are {len(all_ids_from_playlist):,} videos in all the playlists')


    ## Exceptions
    skip_handle_shorts_path = files_manager.exception_folder / 'skip_shorts_handle.txt'
    skip_shorts_handle = files_manager.get_elements_from_file(skip_handle_shorts_path)

    skip_long_videos_60m_path = files_manager.exception_folder / 'skip_long_videos_60m.txt'
    skip_long_videos = files_manager.get_elements_from_file(skip_long_videos_60m_path, create_file = True)

    skip_live_handle = files_manager.exception_folder /'skip_live_handle.txt'
    skip_liveStreamingDetails_handle = files_manager.get_elements_from_file(skip_live_handle, create_file = True)

    skip_title_path = files_manager.exception_folder /'skip_title.txt'
    titles_list = files_manager.get_elements_from_file(skip_title_path, create_file = True)

    only_add_long_videos_path = files_manager.exception_folder / 'only_add_long_videos.txt'
    only_long_videos = files_manager.get_elements_from_file(only_add_long_videos_path, create_file = True)

    WL_shorts_path = files_manager.exception_folder / 'WL_shorts.txt'
    WL_shorts = files_manager.get_elements_from_file(WL_shorts_path, create_file = True)

    missing_video_ids = files_manager.find_missing_elements(all_ids_from_playlist)
    if missing_video_ids:
        print(f'There are {len(missing_video_ids)} videos not in the files')

    saved_quota = 0
    manually_added = defaultdict(list)

    not_in_df = []
    for video_id in missing_video_ids:
        response = yt.get_response_video_id(video_id)
        items = response.get('items',[])
        if not items:
            continue
        snippet = items[0].get('snippet', {})
        channelId = snippet.get('channelId', "")
        if channelId in files_manager.YT_content_creators['channelID'].values:
            handle = files_manager.YT_content_creators[files_manager.YT_content_creators['channelID'] == channelId]['Handle'].iloc[0]
            handle_path = files_manager.content_creator_folder / f'{handle}.txt'
            files_manager.add_element_to_file(handle_path, video_id, sort_list = False, print_statement = True)
            manually_added[handle].append(response)
            saved_quota += 49
        else:
            not_in_df.append(response)
            
    print(f'The saved quota was: {saved_quota:,}')
    if not_in_df:
        print('Handles not in Data Frame')
        for response in not_in_df:
            video_info = response_mnr.get_video_info(response)
            print(f"\t{video_info['title']}")
            print(f"\t{video_info['channelTitle']}")
            print(f"\t{video_info['publishedAt']}")
            print(f"\t{yt_url}{video_info['video_id']}")
            print('*'*50)

    if manually_added:
        print('Videos IDs that were manually added to any playlist')
        for handle in manually_added:
            responses = manually_added[handle]
            print(handle)
            for response in responses:
                video_info = response_mnr.get_video_info(response)
                print(f"\t{video_info['title']}")
                print(f"\t{video_info['publishedAt']}")
                print(f"\t{yt_url}{video_info['video_id']}")
                print('*'*50)
            print('-'*50)

    # Get the new IDs
    was_braked = False
    num_rows = len(YT_content_creators_iter)
    digits = len(str(num_rows))
    message = ''
    liveStream = []
    start = time.time()
    for row in YT_content_creators_iter.itertuples():
        # if was_braked:
        #     break
        handle = row.Handle
        channelName = row.channelName
        channelID = row.channelID
        uploadsID = row.uploadsID

        print(" "*len(message), end='\r')
        message = f'{row.Index + 1:0{digits}d} / {num_rows}: {channelName}'
        print(message, end='\r')
        videos_ids = yt.get_all_ids_playlist(uploadsID, 1)
        videos_ids.reverse()
        file_path = files_manager.content_creator_folder / f'{handle}.txt'
        handle_ids = files_manager.get_elements_from_file(file_path, create_file = True)
        playlist_key = next((key for key, handles in youtube_playlists.items() if handle in handles.get('Handles',[])), None)

        for index, video_id in enumerate(videos_ids,):
            if video_id not in handle_ids: #or video_id not in all_ids_from_playlist:
                response_i = time.time()
                response = yt.get_response_video_id(video_id)
                video_id_info = response_mnr.get_video_info(response)
                video_id_info['file_path'] = file_path
                video_id_info['response'] = response

                if not video_id_info:
                    continue            
                elif video_id_info['liveBroadcastContent'] == 'upcoming' or  video_id_info['duration'] == 0:
                    continue
                elif response_mnr.is_restricted(response):
                    files_manager.add_element_to_file(file_path, video_id, False)
                    response_mnr.add_response_df(files_manager.restriction_folder / f'{handle}.csv', response)
                    
                elif video_id_info['liveStreamingDetails'] and handle in skip_liveStreamingDetails_handle:
                    files_manager.add_element_to_file(file_path,video_id, False)
                    liveStream.append(video_id)  
                
                elif (handle in only_long_videos and duration < 35*60) or \
                any(functions.remove_accents(t.lower()) in functions.remove_accents(video_id_info["title"].lower()) for t in titles_list) or \
                (handle in skip_long_videos and video_id_info['duration'] >= 60*60) or video_id_info['duration'] >= 60*60*3:
                    files_manager.add_element_to_file(file_path,video_id, False)
                else:
                    short = functions.is_short(video_id)
                    if short is None:
                        was_braked = True
                        # break
                    elif short is True:
                        if handle in WL_shorts:
                            youtube_playlists[WL_shorts_playlist]['new_video_ids'].append(video_id_info)
                        elif handle not in skip_shorts_handle:
                            youtube_playlists[shorts_playlist_name]['new_video_ids'].append(video_id_info)
                        else:
                            files_manager.add_element_to_file(file_path,video_id, False)
                    elif playlist_key:
                        youtube_playlists[playlist_key]['new_video_ids'].append(video_id_info)
                    else:
                        youtube_playlists[other_playlist_name]['new_video_ids'].append(video_id_info)
        if was_braked:
            pass
            # break                 
    
    print(" "*len(message), end='\r')
    print(f'Duration to getting the new IDs => {functions.duration_string(time.time() - start)}')
    if not was_braked:
        total_duration = sum(video_id['duration'] for playlist in youtube_playlists for video_id in youtube_playlists[playlist]['new_video_ids'])
        print(f"Duration of all the new Video IDs => {functions.duration_string(total_duration)}")

        total_videos = sum(len(youtube_playlists[playlist]['new_video_ids']) for playlist in youtube_playlists)
        print(f'There are {total_videos} total videos to add')
    else:
        print('There is an error with the request function. You might be blocked')
        pass

    quota_limit = 9000
    was_braked = False
    message = ''
    added_videos = defaultdict(list)
    not_added_videos = defaultdict(list)
    quota_i = files_manager.get_today_quota(False)
    for playlist in youtube_playlists:
        new_video_ids = youtube_playlists[playlist]['new_video_ids']
        playlist_id = youtube_playlists[playlist]["Playlist_ID"]
        new_video_ids.sort(key= lambda x: x['publishedAt'])
        if files_manager.get_today_quota() > quota_limit:
            add_video_to_playlist = False
            was_braked = True
            # break
        if new_video_ids:
            if not playlist_id:
                response_playlist = yt.create_private_playlist(playlist, playlist)
                playlist_id = response_playlist.get('id', "")
                youtube_playlists[playlist]["Playlist_ID"] = playlist_id

                if not playlist_id:
                    continue
                if "shorts" in playlist.lower():
                    for video_id in vertical_video_id:
                        yt.add_video_to_playlist(playlist_id, video_id)
                
            for video_info in new_video_ids:
                file_path = video_info['file_path']
                video_id = video_info['video_id']
                print(' '*len(message), end='\r')
                message = f'Adding {video_id} from {file_path.stem} to the playlist {playlist}'
                print(message, end='\r')
                if not add_video_to_playlist:
                    not_added_videos[playlist].append(video_info)
                    

                elif files_manager.get_today_quota() > quota_limit:
                    add_video_to_playlist = False
                    was_braked = True
                    # break

                elif add_video_to_playlist and video_id not in youtube_playlists[playlist]['video_ids']:# and 
                    if yt.add_video_to_playlist(playlist_id, video_id):
                        files_manager.add_element_to_file(file_path, video_id, False, False)
                        youtube_playlists[playlist]['video_ids'].append(video_id)
                        added_videos[playlist].append(video_info)
                else:
                    pass
    print(' '*len(message), end='\r')         
    if was_braked:
        print(f'The process was interrupted. The last video is was {video_id} from {file_path.name}')

    consumed_quota = files_manager.get_today_quota(False) - quota_i
    print(f'It was consumed {consumed_quota:,} quotas in the adding process and the final quota is {files_manager.get_today_quota(False):,}')
    if added_videos:
        alignment = max(len(playlist) for playlist in added_videos)
        sorted_keys = sorted(added_videos, key=lambda x:sum(video['duration'] for video in added_videos[x]), reverse=True)
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')  

        val_alignment = 2
        for playlist in sorted_keys:
            duration = sum(video['duration'] for video in added_videos[playlist])
            num_videos = len(added_videos[playlist])
            bold_key = f"\033[1;4m{playlist}:\033[0m" 
            extra_alignment = len(bold_key) - len(ansi_pattern.sub('', bold_key)) + 1
            print(f'{bold_key:<{alignment + extra_alignment}} {num_videos:>{val_alignment}} {functions.duration_string(duration)}')

    if not_added_videos:
        print("Videos that were not added to any playlist")
        alignment = max(len(playlist) for playlist in not_added_videos)
        sorted_keys = sorted(not_added_videos, key=lambda x:sum(video['duration'] for video in added_videos[x]), reverse=True)
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')  

        val_alignment = 2
        for playlist in sorted_keys:
            duration = sum(video['duration'] for video in not_added_videos[playlist])
            num_videos = len(not_added_videos[playlist])
            bold_key = f"\033[1;4m{playlist}:\033[0m" 
            extra_alignment = len(bold_key) - len(ansi_pattern.sub('', bold_key)) + 1
            print(f'{bold_key:<{alignment + extra_alignment}} {num_videos:>{val_alignment}} {functions.duration_string(duration)}')



if __name__ == "__main__":
    main()
    # yt = YouTubeManager()
    # playlist_names = yt.get_all_playlists()
    # print(playlist_names)
