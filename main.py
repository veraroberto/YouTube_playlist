
from YouTube import YouTubeManager

from filesManager import filesManager
from paths import (content_creator_folder,
                   exception_folder,
                   playlist_folder,
                   restriction_folder,
                   html_folder,
                   yt_url,
                   yt_channel,
                   clear_row)
from typing import cast
from response import response_manager

# from itertools import count
from pathlib import Path
from collections import defaultdict

# import pandas as pd

import time
import re
import pyperclip
from datetime import date
import json
import random

from app_functions import (choose_option,
                           clear_terminal,
                           remove_accents,
                           duration_string,
                           is_short,
                           create_bookmarks)
from manage_video_ids import (add_video_manually,
                              manage_exceptions,
                              get_video_id)
from df_manager import df_manager

fm = filesManager()
yt = YouTubeManager()
response_mnr = response_manager()
df_mnr = df_manager()


def main(add_video_ids_to_playlist: bool = True) -> None:
    YT_df = fm.YT_content_creators
    YT_content_creators_iter = df_mnr.get_df_to_iterate(playlist_folder, YT_df)
    if YT_content_creators_iter is None:
        return
    ## Creates the Dictionary of the Playlists
    playlist_names = yt.get_all_playlists()
    if not playlist_names:
        print('There was not possible to get the playlist')
        return

    youtube_names = [file.stem.replace('_', ' ').strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
    youtube_playlists = defaultdict(lambda:
                                    {"Handles":[],
                                    "Playlist_ID": "",
                                    "video_ids": [],
                                    "new_video_ids": [],
                                    })

    shorts_playlist_name = 'Shorts To Watch'
    other_playlist_name = 'Videos To Watch'
    vertical_video_id = fm.get_elements_from_file(exception_folder / "vertical_video.txt", create_file=False)
    special_playlist = [other_playlist_name, shorts_playlist_name]
    # youtube_names.extend({'Path': None, 'Name': playlist} for playlist in special_playlist)
    youtube_names.extend(special_playlist)

    for playlist in youtube_names:
        file_path = playlist_folder / f'{playlist.replace(" ","_")}.txt'
        if file_path.exists():
            handles = file_path.read_text(encoding="utf-8").splitlines()
            youtube_playlists[playlist]['Handles'].extend(handles)
        #Getting the Playlist ID
        playlist_id = next((d["id"] for d in playlist_names if playlist in d.values()), None)
        youtube_playlists[playlist]['Playlist_ID'] = playlist_id

        if playlist_id:
            video_ids = yt.get_all_ids_playlist(playlist_id, 300, count_repeated=True)

            if not video_ids:
                if playlist_id in YT_df['uploads'].values:
                    channelId = YT_df[YT_df['uploads'] == playlist_id]['channelId'].iloc[0]
                    print(f"{yt_channel}{channelId}")
            youtube_playlists[playlist]['video_ids'].extend(video_ids)

    all_ids_from_playlist = [video_id for playlist in youtube_playlists.values() for video_id in playlist['video_ids']]
    print(f'There are {len(all_ids_from_playlist):,} videos in all the playlists')

    ## Exceptions
    skip_handle_shorts_path = exception_folder / 'skip_shorts_handle.txt'
    skip_shorts_handle = fm.get_elements_from_file(skip_handle_shorts_path)

    short_in_playlist_path = exception_folder / "short_in_playlist.txt"
    short_in_playlist = fm.get_elements_from_file(short_in_playlist_path, create_file=True)

    skip_long_videos_60m_path = exception_folder / 'skip_long_videos_60m.txt'
    skip_long_videos = fm.get_elements_from_file(skip_long_videos_60m_path, create_file = True)

    skip_live_handle = exception_folder /'skip_live_handle.txt'
    skip_liveStreamingDetails_handle = fm.get_elements_from_file(skip_live_handle, create_file = True)

    only_add_long_videos_path = exception_folder / 'only_add_long_videos.txt'
    only_long_videos = fm.get_elements_from_file(only_add_long_videos_path, create_file = True)

    more_iterations_path = exception_folder / "more_iterations.txt"
    more_iterations = fm.get_elements_from_file(more_iterations_path, create_file=True)

    handle_dict_name_excepts_path = exception_folder / "handle_dict_name_excepts.json"
    handle_dict_name_excepts = fm.read_json(handle_dict_name_excepts_path, True)

    missing_video_ids = fm.find_missing_elements(all_ids_from_playlist)
    missing_video_ids = [x for x in missing_video_ids if x not in vertical_video_id]

    if missing_video_ids:
        print(f'There are {len(missing_video_ids)} videos not in the files')

    saved_quota = 0
    manually_added = defaultdict(list)

    not_in_df = []
    for video_id in missing_video_ids:
        response = yt.get_response_video_id(video_id)
        if response is None:
            continue
        items = response.get('items',[])
        if not items:
            continue
        snippet = items[0].get('snippet', {})
        channelId = snippet.get('channelId', "")
        if channelId in YT_df['channelId'].values:
            handle = YT_df[YT_df['channelId'] == channelId]['Handle'].iloc[0]
            handle_path = content_creator_folder / f'{handle}.txt'
            fm.add_element_to_file(handle_path, video_id, sort_list = False, print_statement = True)
            manually_added[handle].append(response)
            saved_quota += 49

        else:
            not_in_df.append(response)

    print(f'The saved quota was: {saved_quota:,}')
    if not_in_df:
        print('Handles not in Data Frame')
        not_in_df_dict = {}
        for index, response in enumerate(not_in_df,1):
            video_info = response_mnr.get_video_info(response)
            if video_info is None:
                continue
            title = video_info['title']
            channelTitle = video_info['channelTitle']
            publishedAt = video_info['publishedAt']
            video_id = video_info['video_id']
            print(f"\t{title}")
            print(f"\t{channelTitle}")
            print(f"\t{publishedAt}")
            print(f"\t{yt_url}{video_id}")
            not_in_df_dict[video_id] = f'{index:02d} {publishedAt} {title}'
            print('*'*50)
        today = date.today()
        formatted_date = today.strftime("%Y-%m-%d")
        create_bookmarks(not_in_df_dict,Path(f'{formatted_date} Videos not in DF.html'),yt_url,"Not in DF")

    if manually_added:
        print('Videos IDs that were manually added to any playlist')
        for handle in manually_added:
            responses = manually_added[handle]
            print(handle)
            for response in responses:
                video_info = response_mnr.get_video_info(response)
                if video_info is None:
                    continue
                print(f"\t{video_info['title']}")
                print(f"\t{video_info['publishedAt']}")
                print(f"\t{yt_url}{video_info['video_id']}")
                print('*'*50)
            print('-'*50)

    # Get the new IDs
    was_braked = False
    num_rows = len(YT_content_creators_iter)
    digits = len(str(num_rows))
    start = time.time()
    for row in YT_content_creators_iter.itertuples():
        if was_braked:
            break
        handle = row.Handle
        channelTitle = row.channelTitle
        channelId = row.channelId
        uploads = cast(str, row.uploads)
        message = f'{ cast(int, row.Index) + 1:0{digits}d} / {num_rows}: {channelTitle} line 193'
        print(message + clear_row, end='\r')
        iterations = 1
        if handle in more_iterations:
            """
            In some Podcasts the IDs are not sorted by by date in descending order, so it would need
            more iterations to get the new video IDs
            """
            iterations = 10
        videos_ids = yt.get_all_ids_playlist(uploads, iterations)
        if not videos_ids:
            if videos_ids is None:
                continue
            elif uploads in YT_df['uploads'].values:
                channelId = YT_df[YT_df['uploads'] == uploads]['channelId'].iloc[0]
                channelTitle = YT_df[YT_df['uploads'] == uploads]['channelTitle'].iloc[0]
                print(f"The Channel {channelTitle} might be deleted: {yt_channel}{channelId}\033[K")

        videos_ids.reverse()
        file_path = content_creator_folder / f'{handle}.txt'
        handle_ids = fm.get_elements_from_file(file_path, create_file = True)
        playlist_key = next((key for key, handles in youtube_playlists.items() if handle in handles.get('Handles',[])), None)

        for index, video_id in enumerate(videos_ids,1):
            if video_id not in handle_ids:
                response = yt.get_response_video_id(video_id)
                if not response:
                    print(f'{handle} {yt_url}{video_id}')
                    fm.add_element_to_file(file_path, video_id, False)
                    continue
                video_id_info = response_mnr.get_video_info(response)
                video_id_info['file_path'] = file_path
                video_id_info['response'] = response
                title = video_id_info["title"]
                exception_title = handle_dict_name_excepts.get(handle, [])
                clean_title = remove_accents(title.lower())
                if video_id_info['liveBroadcastContent'] == 'upcoming' or  video_id_info['duration'] == 0:
                    continue
                elif response_mnr.is_restricted(response):
                    fm.add_element_to_file(file_path, video_id, False)
                    response_mnr.add_response_df(restriction_folder / f'{handle}.csv', response)

                elif video_id_info['liveStreamingDetails'] and handle in skip_liveStreamingDetails_handle:
                    fm.add_element_to_file(file_path,video_id, False)
                elif handle in handle_dict_name_excepts and \
                    any(remove_accents(t.lower()) in clean_title for t in exception_title):
                    skipping_title = next((title for title in exception_title if title in clean_title), "")
                    bold_word = f"\033[1;4m{skipping_title}\033[0m\033[K"
                    print(f'Skipping the video for from \x1b[1;31m {handle}\033[m the title: {bold_word}')
                    response_mnr.get_video_info(response, True, True)
                    fm.add_element_to_file(file_path,video_id, False)
                    print('*'*100)

                elif (handle in only_long_videos and video_id_info['duration'] < 35*60) or \
                (handle in skip_long_videos and video_id_info['duration'] >= 60*60) or (video_id_info['duration'] >= 60*60*3):
                    fm.add_element_to_file(file_path,video_id, False)
                else:
                    short = is_short(video_id)
                    time.sleep(random.uniform(0.5, 1))
                    if short is None:
                        was_braked = True
                        break
                    elif short is True and handle not in short_in_playlist:
                        if handle not in skip_shorts_handle:
                            youtube_playlists[shorts_playlist_name]['new_video_ids'].append(video_id_info)
                        else:
                            fm.add_element_to_file(file_path,video_id, False)
                    elif playlist_key:
                        youtube_playlists[playlist_key]['new_video_ids'].append(video_id_info)
                    else:
                        youtube_playlists[other_playlist_name]['new_video_ids'].append(video_id_info)

        if was_braked:
            break

    print(f'Duration to getting the new IDs => {duration_string(time.time() - start)}' + clear_row)
    if not was_braked:
        total_duration = sum(video_id['duration'] for playlist in youtube_playlists for video_id in youtube_playlists[playlist]['new_video_ids'])
        print(f"Duration of all the new Video IDs => {duration_string(total_duration)}")

        total_videos = sum(len(youtube_playlists[playlist]['new_video_ids']) for playlist in youtube_playlists)
        print(f'There are {total_videos} total videos to add')
    else:
        print('There is an error with the request function. You might be blocked')

    quota_limit = 9700
    was_braked = False
    break_message = ""
    added_videos = defaultdict(list)
    not_added_videos = defaultdict(list)
    quota_i = fm.get_today_quota(False)
    for playlist in youtube_playlists:
        new_video_ids = youtube_playlists[playlist]['new_video_ids']
        playlist_id = youtube_playlists[playlist]["Playlist_ID"]
        new_video_ids.sort(key= lambda x: x['publishedAt'])
        if fm.get_today_quota() > quota_limit:
            add_video_ids_to_playlist = False
            was_braked = True
        if new_video_ids:
            if not playlist_id and not was_braked and add_video_ids_to_playlist:
                response_playlist = yt.create_private_playlist(playlist, playlist)
                time.sleep(1)
                if not response_playlist:
                    print(f'There was not possible to create the Playlist {playlist}')
                    continue
                playlist_id = response_playlist.get('id')
                youtube_playlists[playlist]["Playlist_ID"] = playlist_id
                if not playlist_id:
                    continue
                if "shorts" in playlist.lower():
                    for video_id in vertical_video_id:
                        yt.add_video_to_playlist(playlist_id, video_id)

            for video_info in new_video_ids:
                file_path = video_info['file_path']
                video_id = video_info['video_id']
                message = f'Adding {video_id} from {file_path.stem[0:50]} to the playlist {playlist}' + clear_row +"line 309"
                print(message + clear_row, end='\r')
                if not add_video_ids_to_playlist:
                    not_added_videos[playlist].append(video_info)
                elif fm.get_today_quota() > quota_limit:
                    add_video_ids_to_playlist = False
                    break_message = f'The process was interrupted. The last video is {video_id} from {file_path.name}' + clear_row
                    was_braked = True
                elif add_video_ids_to_playlist and video_id not in youtube_playlists[playlist]['video_ids']:# and
                    if yt.add_video_to_playlist(playlist_id, video_id):
                        fm.add_element_to_file(file_path, video_id, False, False)
                        youtube_playlists[playlist]['video_ids'].append(video_id)
                        added_videos[playlist].append(video_info)
                else:
                    pass
    if was_braked and break_message:
        print(break_message)

    consumed_quota = fm.get_today_quota(False) - quota_i
    print(f'It was consumed {consumed_quota:,} quotas in the adding process\033[K')
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
            print(f'{bold_key:<{alignment + extra_alignment}} {num_videos:>{val_alignment}} {duration_string(duration)}')

    if not_added_videos:
        print("Videos that were not added to any playlist")
        alignment = max(len(playlist) for playlist in not_added_videos)
        sorted_keys = sorted(not_added_videos, key=lambda x:sum(video['duration'] for video in added_videos[x]), reverse=True)
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')

        val_alignment = 2
        for playlist in sorted_keys:
            print(f'{playlist}:')
            responses = sorted(not_added_videos[playlist], key= lambda x: x['publishedAt'])
            for index, response in enumerate(responses, 1):
                video_id = response['video_id']
                print(f'\t{index:02d} {yt_url}{video_id}')
            print('*'*50)
        if not_added_videos:
            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            print('The following playlist html files were created:')
            for pl_index, playlist in enumerate(not_added_videos, 1):
                print(f'{pl_index:02d} {playlist}')
                urls_dict = {}
                todays_video = not_added_videos[playlist]
                todays_video.sort(key = lambda x: x['response']['items'][0]['snippet']['publishedAt'])
                for index, video in enumerate(todays_video, 1):
                    publishedAt = video['response']['items'][0]['snippet']['publishedAt']
                    title = video['title']
                    video_id = video['video_id']
                    urls_dict[video_id] = f'{index:02d} {title}'
                file_html = html_folder / f'{formatted_date}_{playlist.replace(" ", "_")}.html'
                create_bookmarks(urls_dict, file_html, yt_url,playlist)
        return

def add_video() -> None:
    while True:
        add_video_manually(get_video_id(input("Video ID or URL: ")))
        if not choose_option([True, False], message="Add another video ID: "):
            break
    return

def manage_df() -> None:
    functions_dict = {
        'Delete Information from files': df_mnr.delete_information_in_files,
        'Add new row to the Data Frame': df_mnr.add_row_df
    }
    list_keys = list(functions_dict.keys())
    function = choose_option(list_keys,'Choose a Function: ')
    if not isinstance(function, str):
        print('Doing Nothing')
        return
    while True:
        functions_dict[function]()
        if not choose_option([True, False], f'Continue {function}'):
            break
    return

def manage_playlist() -> None:
    options = [
        "Move a handle to a new Playlist",
        "Delete handles from all playlist",
        "Delete a playlist"
    ]
    option_choosen = choose_option(options, "Playlist Manager: ")
    if option_choosen is None:
        return
    else:
        if option_choosen == options[2]:
            playlist_name = input('Name a list to Delete: ')
            plalylist_path = playlist_folder / f"{playlist_name.strip().replace(' ', '_')}.txt"
            if not plalylist_path.exists():
                print(f"The Playlist {playlist_name} doesn't exist.")
            else:
                try:
                    playlist_handle = fm.get_elements_from_file(plalylist_path)
                    plalylist_path.unlink(missing_ok=True)
                    print(f"The Playlist {playlist_name} contains the handles: {', '.join(playlist_handle)}  and was deleted")
                except Exception as e:
                    print(f"{plalylist_path.name} {e}")
        else:
            handle = input("Handle to manage: ").strip().lower()
            if handle not in df_mnr.handles_df:
                print('The handle is not present in the Data Frame')
                return
            fm.delete_string_from_txt_files(playlist_folder, handle)
            if option_choosen == options[0]:            
                files = [file.stem for file in playlist_folder.iterdir() if not file.name.startswith('.') and file.suffix.lower() == '.txt']
                files.append('Create New Playlist')
                choosen_file = choose_option(files, "Add the handle to the Playlist")
                if choosen_file is None:
                    print('There was an error, the handle was not added to any playlist')
                    return
                elif choosen_file == files[-1]:
                    new_playlist = input('New Playlist name: ').strip().replace(' ','_')
                    file_path = playlist_folder / f'{new_playlist}.txt'
                else:
                    file_path = playlist_folder / f'{choosen_file}.txt'
                    fm.add_element_to_file(file_path, handle, True, True, True)



    return

def add_video_list() -> None:
    input('Click enter when the list of links is in the clipboard ')
    links_list = pyperclip.paste().splitlines()
    for video_id in links_list:
        add_video_manually(get_video_id(video_id))
    return

if __name__ == "__main__":
    function_dict = {"Main": lambda: main(),
                     "Only get current quota": None,
                     "Manually add Video": lambda:  add_video(),
                     "Only create the HTML files and don't add the videos": lambda: main(False),
                     "Exception Manager": lambda: manage_exceptions(),
                     "Add / Remove row from DF": lambda: manage_df(),
                     "Playlist Manager": lambda: manage_playlist(),
                     "Add a list of videos from the Clipboard": lambda: add_video_list(),
                     }

    function_choosen = choose_option(list(function_dict.keys()), "Choose an action")
    clear_terminal()
    if function_choosen and function_dict[function_choosen]:
        function_dict[function_choosen]()
    
    fm.get_today_quota(True)

