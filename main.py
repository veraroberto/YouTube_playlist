
from YouTube import YouTubeManager

from filesManager import filesManager
from paths import (content_creator_folder,
                   exception_folder,
                   playlist_folder,
                   restriction_folder,
                   html_folder,
                   yt_url,
                   yt_channel,
                   clear_row,
                   reset_format,
                   shorts_playlist_name,
                   other_playlist_name)
from typing import cast
from response import response_manager

# from itertools import count
from pathlib import Path
from collections import defaultdict
from colors import Color
# import pandas as pd

import time, inspect, re, pyperclip, random

from datetime import date

formats_color = Color()
from app_functions import (choose_option,
                           clear_terminal,
                           remove_accents,
                           duration_string,
                           is_short,
                           create_bookmarks,
                           pluralize)
from manage_videoIds import (add_video_manually,
                              manage_exceptions,
                              get_videoId)
from df_manager import df_manager

fm = filesManager()
yt = YouTubeManager()
response_mnr = response_manager()
df_mnr = df_manager()


def main(add_videoIds_to_playlist: bool = True) -> None:
    YT_df = fm.YT_content_creators
    YT_content_creators_iter = df_mnr.get_df_to_iterate(playlist_folder, YT_df)
    if YT_content_creators_iter is None:
        return
    ## Creates the Dictionary of the Playlists
    playlist_names = yt.get_all_playlists()
    if not playlist_names:
        print('There was not possible to get the playlists')
        return


    youtube_names = [file.stem.replace('_', ' ').strip() for file in playlist_folder.iterdir() if file.suffix == '.txt']
    youtube_playlists = defaultdict(lambda:
                                    {"customUrls":[],
                                    "Playlist_ID": "",
                                    "videoIds": [],
                                    "new_videoIds": [],
                                    })


    vertical_videoId = fm.get_elements_from_file(exception_folder / "vertical_video.txt", create_file=False)
    special_playlist = [other_playlist_name, shorts_playlist_name]
    # youtube_names.extend({'Path': None, 'Name': playlist} for playlist in special_playlist)
    youtube_names.extend(special_playlist)

    for playlist in youtube_names:
        file_path = playlist_folder / f'{playlist.replace(" ","_")}.txt'
        if file_path.exists():
            customUrls = file_path.read_text(encoding="utf-8").splitlines()
            youtube_playlists[playlist]['customUrls'].extend(customUrls)
        #Getting the Playlist ID
        playlist_id = next((d["id"] for d in playlist_names if playlist in d.values()), None)
        youtube_playlists[playlist]['Playlist_ID'] = playlist_id

        if playlist_id:
            # videoIds = yt.get_all_ids_playlist(playlist_id, 300, count_repeated=True)
            upload_responses = yt.get_all_ids_playlist(playlist_id, max_iterations=300, count_repeated=True)
            videoIds = [item.get('videoId') for item in upload_responses]
            
            if not videoIds:
                if playlist_id in YT_df['uploads'].values:
                    channelId = YT_df[YT_df['uploads'] == playlist_id]['channelId'].iloc[0]
                    print(f"{yt_channel}{channelId}")
            youtube_playlists[playlist]['videoIds'].extend(videoIds)

    all_ids_from_playlist = [videoId for playlist in youtube_playlists.values() for videoId in playlist['videoIds']]
    print(f'There are {len(all_ids_from_playlist):,} videos in all the playlists')

    ## Exceptions
    skip_customUrl_shorts_path = exception_folder / 'skip_shorts_customUrl.txt'
    skip_shorts_customUrl = fm.get_elements_from_file(skip_customUrl_shorts_path, create_file=True)

    short_in_playlist_path = exception_folder / "short_in_playlist.txt"
    short_in_playlist = fm.get_elements_from_file(short_in_playlist_path, create_file=True)

    skip_long_videos_60m_path = exception_folder / 'skip_long_videos_60m.txt'
    skip_long_videos = fm.get_elements_from_file(skip_long_videos_60m_path, create_file = True)

    skip_live_customUrl = exception_folder /'skip_live_customUrl.txt'
    skip_liveStreamingDetails_customUrl = fm.get_elements_from_file(skip_live_customUrl, create_file = True)

    only_add_long_videos_path = exception_folder / 'only_add_long_videos.txt'
    only_long_videos = fm.get_elements_from_file(only_add_long_videos_path, create_file = True)

    more_iterations_path = exception_folder / "more_iterations.txt"
    more_iterations = fm.get_elements_from_file(more_iterations_path, create_file=True)

    customUrl_dict_name_excepts_path = exception_folder / "customUrl_dict_name_excepts.json"
    customUrl_dict_name_excepts = fm.read_json(customUrl_dict_name_excepts_path, True)

    missing_videoIds = fm.find_missing_elements(all_ids_from_playlist)
    missing_videoIds = [x for x in missing_videoIds if x not in vertical_videoId]

    if missing_videoIds:
        is_are = "is" if len(missing_videoIds) == 1 else "are"
        print(f'There {is_are} {len(missing_videoIds)} {pluralize(len(missing_videoIds), "video")} not in the files')
    saved_quota = 0
    videos_added_manually = 0
    customUrl_not_in_files = []
    initial_quota = fm.get_today_quota(False)
    for videoId in missing_videoIds:
        added_video = add_video_manually(videoId)
        if added_video:
            videos_added_manually += 1
        else:
            customUrl_not_in_files.append(videoId)
    if videos_added_manually:
        consumed_quota = fm.get_today_quota(False) - initial_quota
        saved_quota = videos_added_manually * 50 - consumed_quota
        print(f'The saved quota was: {saved_quota:,} and the videos added manually were: {videos_added_manually}')
    if customUrl_not_in_files:
        digits = len(str(len(customUrl_not_in_files)))
        was_were = "was" if len(customUrl_not_in_files) == 1 else "were"
        print('*'*50 + clear_row)
        print(f'\033[1;32mThe following video {pluralize(len(customUrl_not_in_files), "ID", "IDs")} {was_were} not added because the customUrl is not in the files:{reset_format}\033[0;32m')
        for index, videoId in enumerate(customUrl_not_in_files, 1):
            print(f'{index:0{digits}d} {yt_url}{videoId}')   
        create_bookmarks({videoId: f'{index:0{digits}d} {yt_url}{videoId}' for index, videoId in enumerate(customUrl_not_in_files, 1)}, html_folder / 'missing_videoIds.html', yt_url, 'Missing Video IDs') 
        
        print(reset_format,'*'*50)
    # Get the new IDs
    was_braked = False
    num_rows = len(YT_content_creators_iter)
    digits = len(str(num_rows))
    start = time.time()
    for row in YT_content_creators_iter.itertuples():
        if was_braked:
            break
        customUrl = row.customUrl
        channelTitle = row.channelTitle
        channelId = row.channelId
        uploads = cast(str, row.uploads)
        message = f'{ cast(int, row.Index) + 1:0{digits}d} / {num_rows}: {channelTitle}'
        print(formats_color.CLEAR_LINE, message, end='\r', sep="")
        iterations = 1
        if customUrl in more_iterations:
            """
            In some Podcasts the IDs are not sorted by by date in descending order, so it would need
            more iterations to get the new video IDs
            """
            iterations = 10
        # videos_ids = yt.get_all_ids_playlist(uploads, iterations)
        items_responses = yt.get_all_ids_playlist(uploads, max_iterations=iterations, count_repeated=False)

        if not items_responses:
            if uploads in YT_df['uploads'].values:
                channelId = YT_df[YT_df['uploads'] == uploads]['channelId'].iloc[0]
                channelTitle = YT_df[YT_df['uploads'] == uploads]['channelTitle'].iloc[0]
                print(f"The Channel {channelTitle} with the customUrl {customUrl} might be deleted: {yt_channel}{channelId}\033[K")
            continue

        file_path = content_creator_folder / f'{customUrl}.txt'
        videoIds = fm.get_elements_from_file(file_path, create_file = True)
        playlist_key = next((key for key, customUrls in youtube_playlists.items() if customUrl in customUrls.get('customUrls',[])), None)

        for index, item_response in enumerate(items_responses,1):
            videoId = item_response.get('videoId')
            privacyStatus = item_response.get('privacyStatus')
            if videoId in videoIds or privacyStatus == 'private':
                continue
            elif privacyStatus == 'privacyStatusUnspecified':
                print(f'{formats_color.CLEAR_LINE}{customUrl} Deleted video {yt_url}{videoId}')
                fm.add_element_to_file(file_path, videoId, False)
            elif privacyStatus != "public":
                print(f'{formats_color.CLEAR_LINE}{formats_color.RED}{formats_color.BOLD}{formats_color.UNDERLINE}',
                      f'The video ID {videoId} has a privacy status of {privacyStatus}. The Code needs to be updated in the line {inspect.currentframe().f_lineno}.',
                      f'{formats_color.RESET}', sep="")
            else:
                response = yt.get_response_videoId(videoId)
                videoId_info = response_mnr.get_video_info(response, print_info=False)
                videoId_info['file_path'] = file_path
                videoId_info['response'] = response
                videoId_info['customUrl'] = customUrl
                videoId_info['uploads'] = uploads
                videoId_info['channelTitle'] = channelTitle
                videoId_info['channelId'] = channelId
                title = videoId_info["title"]
                exception_title = customUrl_dict_name_excepts.get(customUrl, [])
                clean_title = remove_accents(title.lower())

                if videoId_info['liveBroadcastContent'] == 'upcoming' or  videoId_info['duration'] == 0:
                    continue
                elif videoId_info['viewCount'] is None:
                    print(f"{formats_color.CLEAR_LINE}",'*'*50, sep="")
                    print(f'The video might be members only. Not adding it to the files')
                    response_mnr.get_video_info(response, print_info=True)
                    fm.add_element_to_file(file_path, videoId, False)
                elif response_mnr.is_restricted(response):
                    fm.add_element_to_file(file_path, videoId, False)
                    response_mnr.add_response_df(restriction_folder / f'{customUrl}.csv', response)

                elif videoId_info['liveStreamingDetails'] and customUrl in skip_liveStreamingDetails_customUrl:
                    fm.add_element_to_file(file_path,videoId, False)
                elif customUrl in customUrl_dict_name_excepts and \
                    any(remove_accents(t.lower()) in clean_title for t in exception_title):
                    skipping_title = next((title for title in exception_title if title in clean_title), "")
                    bold_word = f"\033[1;4m{skipping_title}\033[0m\033[K"
                    print(f'Skipping the video from {formats_color.format(str(customUrl), formats_color.RED, formats_color.BOLD)}. The title contains: {bold_word}')
                    response_mnr.get_video_info(response, True, True)
                    fm.add_element_to_file(file_path,videoId, False)
                    print('*'*100)

                elif (customUrl in only_long_videos and videoId_info['duration'] < 35*60) or \
                (customUrl in skip_long_videos and videoId_info['duration'] >= 60*60) or (videoId_info['duration'] >= 60*60*3):
                    fm.add_element_to_file(file_path,videoId, False)
                else:
                    short = is_short(videoId)
                    time.sleep(random.uniform(0.5, 1))
                    if short is None:
                        was_braked = True
                        break
                    elif short is True and customUrl not in short_in_playlist:
                        if customUrl not in skip_shorts_customUrl:
                            youtube_playlists[shorts_playlist_name]['new_videoIds'].append(videoId_info)
                        else:
                            fm.add_element_to_file(file_path,videoId, False)
                    elif playlist_key:
                        youtube_playlists[playlist_key]['new_videoIds'].append(videoId_info)
                    else:
                        youtube_playlists[other_playlist_name]['new_videoIds'].append(videoId_info)

        if was_braked:
            break
    
    if not was_braked:
        total_duration = sum(videoId['duration'] for playlist in youtube_playlists for videoId in youtube_playlists[playlist]['new_videoIds'])
        if total_duration:
            print(clear_row + f'Duration to getting the new IDs => {duration_string(time.time() - start)}')
            print(f"Duration of all the new Video IDs => {duration_string(total_duration)}")
            total_videos = sum(len(youtube_playlists[playlist]['new_videoIds']) for playlist in youtube_playlists)
            print(f'There are {total_videos} total videos to add')
        else:
            print('There are no new videos to add')
            return
    else:
        print('There is an error with the request function. You might be blocked')

    quota_limit = 9700
    was_braked = False
    break_message = ""
    added_videos = defaultdict(list)
    not_added_videos = defaultdict(list)
    quota_i = fm.get_today_quota(False)
    for playlist in youtube_playlists:
        new_videoIds = youtube_playlists[playlist]['new_videoIds']
        playlist_id = youtube_playlists[playlist]["Playlist_ID"]
        new_videoIds.sort(key= lambda x: x['publishedAt'])
        if fm.get_today_quota() > quota_limit:
            add_videoIds_to_playlist = False
            was_braked = True
        if new_videoIds:
            if not playlist_id and not was_braked and add_videoIds_to_playlist:
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
                    for videoId in vertical_videoId:
                        yt.add_video_to_playlist(playlist_id, videoId)

            for video_info in new_videoIds:
                file_path = video_info['file_path']
                videoId = video_info['videoId']
                message = f'Adding {videoId} from {file_path.stem[0:50]} to the playlist {playlist}' + clear_row
                print(message + clear_row, end='\r')
                if not add_videoIds_to_playlist:
                    not_added_videos[playlist].append(video_info)
                elif fm.get_today_quota() > quota_limit:
                    add_videoIds_to_playlist = False
                    break_message = f'The process was interrupted. The last video is {videoId} from {file_path.name}' + clear_row
                    was_braked = True
                elif add_videoIds_to_playlist and videoId not in youtube_playlists[playlist]['videoIds']:# and
                    if yt.add_video_to_playlist(playlist_id, videoId):
                        fm.add_element_to_file(file_path, videoId, False, False)
                        youtube_playlists[playlist]['videoIds'].append(videoId)
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
                videoId = response['videoId']
                print(f'\t{index:02d} {yt_url}{videoId}')
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
                    videoId = video['videoId']
                    urls_dict[videoId] = f'{index:02d} {title}'
                file_html = html_folder / f'{formatted_date}_{playlist.replace(" ", "_")}.html'
                create_bookmarks(urls_dict, file_html, yt_url,playlist)
        return

def add_video() -> None:
    while True:
        add_video_manually(get_videoId(input("Video ID or URL: ")))
        if not choose_option([True, False], message="Add another video ID: "):
            break
    return

def manage_df() -> None:
    functions_dict = {
        'Add new row to the Data Frame': df_mnr.add_row_df,
        'Delete Information from files': df_mnr.delete_information_in_files,
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
        "Move a customUrl to a new Playlist",
        "Delete customUrls from all playlist",
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
                    playlist_customUrl = fm.get_elements_from_file(plalylist_path)
                    plalylist_path.unlink(missing_ok=True)
                    print(f"The Playlist {playlist_name} contains the customUrls: {', '.join(playlist_customUrl)}  and was deleted")
                except Exception as e:
                    print(f"{plalylist_path.name} {e}")
        else:
            customUrl = input("customUrl to manage: ").strip().lower()
            if customUrl not in df_mnr.customUrls_df:
                print('The customUrl is not present in the Data Frame')
                return
            fm.delete_string_from_txt_files(playlist_folder, customUrl)
            if option_choosen == options[0]:            
                files = [file.stem for file in playlist_folder.iterdir() if not file.name.startswith('.') and file.suffix.lower() == '.txt']
                files.append('Create New Playlist')
                choosen_file = choose_option(files, "Add the customUrl to the Playlist")
                if choosen_file is None:
                    print('There was an error, the customUrl was not added to any playlist')
                    return
                elif choosen_file == files[-1]:
                    new_playlist = input('New Playlist name: ').strip().replace(' ','_')
                    file_path = playlist_folder / f'{new_playlist}.txt'
                else:
                    file_path = playlist_folder / f'{choosen_file}.txt'
                    fm.add_element_to_file(file_path, customUrl, True, True, True)



    return

def add_video_list() -> None:
    input('Click enter when the list of links is in the clipboard ')
    links_list = pyperclip.paste().splitlines()
    for videoId in links_list:
        add_video_manually(get_videoId(videoId))
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
                     "Exit": None
                     }

    function_choosen = choose_option(list(function_dict.keys()), "Choose an action")
    clear_terminal()
    if function_choosen and function_dict[function_choosen]:
        function_dict[function_choosen]()
    else:
        print(f'Doing Nothing {clear_row}')
    
    fm.get_today_quota(True)



