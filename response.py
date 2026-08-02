import isodate
import pandas as pd
from filesManager import filesManager
from pathlib import Path
from app_functions import (duration_string,
                           print_dictionary)

import json
import re
from paths import (yt_playlist)
# from urllib.request import urlopen

default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published 
class response_manager():
    def __init__(self):
        self.files_manager = filesManager()
        # self.youtube = YouTubeManager()
        # self.data = json.load(urlopen('https://ipinfo.io/'))
        # self.current_country = self.data.get('country')
        self.current_country = "MX"
        
    def get_video_info(self, response:  dict, print_info: bool = False, del_extra_keys: bool = False) -> dict:
        items = response.get('items', [])
        if not items:
            return {}
        video_id = response['items'][0]['id']
        
        snippet = items[0].get('snippet', {})
        publishedAt = snippet.get('publishedAt', default_date)  #Timestamp of the first YouTube video ever published 
        title = snippet.get('title', "")
        channelTitle = snippet.get('channelTitle',"")
        channelId = snippet.get('channelId', "")
        contentDetails = items[0].get('contentDetails', {})
        regionRestriction = contentDetails.get('regionRestriction',{})

        duration_iso = contentDetails.get('duration', 'PT0S')
        duration = isodate.parse_duration(duration_iso).total_seconds()
        liveBroadcastContent = snippet.get('liveBroadcastContent', None)
        liveStreamingDetails = items[0].get('liveStreamingDetails', None)
        video_id_info = {'video_id': video_id,
                         'channelTitle': channelTitle,
                         'channelId': channelId,
                         'publishedAt': publishedAt,
                         'title': title,
                         'duration' : duration,
                         'liveBroadcastContent': liveBroadcastContent,
                         'liveStreamingDetails': liveStreamingDetails,
                         'regionRestriction':regionRestriction
                        }
        if del_extra_keys:
            if not regionRestriction:
                del video_id_info['regionRestriction']
            if video_id_info['liveBroadcastContent'] == "none":
                del video_id_info['liveBroadcastContent']
            if video_id_info['liveStreamingDetails'] is None:
                del video_id_info['liveStreamingDetails']
        if print_info:
            align = max(len(k) for k in video_id_info)
            for k in video_id_info:

                if k == 'duration':
                    print(f"{k+": ":<{align + 2}} {duration_string(video_id_info[k])}")
                elif isinstance(video_id_info[k], dict) and video_id_info[k]:
                    print(k+": ")
                    align_2 = max(len(k_2) for k_2 in video_id_info[k])
                    for key, val in video_id_info[k].items():
                        if isinstance(val, list):
                            print(f'{" " *(align + 3)}{key+": ":<{align_2 + 2}} {", ".join(val)}')
                        else:
                            print(f'{" " *(align + 3)}{key+": ":<{align_2 + 2}} {val}')
                else:
                    print(f"{k+": ":<{align + 2}} {video_id_info[k]}")
        return video_id_info

    def get_channel_info(self, channel_response: dict) -> dict:
        items = channel_response.get('items', {})
        if not items:
            print("The Channel Doesn't have information ")
            print(channel_response)
            return
        channelId = items[0].get('id', "")
        snippet = items[0].get('snippet', {})
        if not snippet:
            print('There is no snippet in the channel')
            return
        contentDetails = items[0].get('contentDetails', {})
        if not contentDetails:
            print('There is not contentDetails')
            return
        channelTitle = snippet.get('title', "")
        relatedPlaylists = contentDetails.get('relatedPlaylists', {})
        if not relatedPlaylists:
            print('There is no relatedPlaylists')
            return
        
        uploads = relatedPlaylists.get('uploads', None)
        customUrl = snippet.get('customUrl', "").replace('@', "")


        channel_info = {
            'customUrl': customUrl,
            'channelId': channelId,
            'channelTitle': channelTitle,
            'uploads': uploads,

        }
        return channel_info

    def get_playlist_info(self, playlist_response: dict, print_info: bool = False) -> dict:
        items = playlist_response.get('items',{})
        playlist_id = items[0].get('id','')
        if not items:
            print(f'There no items in the playlist')
            print(playlist_response)
            return
        snippet = items[0].get('snippet', {})
        if not snippet:
            print(f'There is no snippet in the Playlist Resposnse')
            return
        channelId = snippet.get('channelId',"")
        title = snippet.get('title')
        customUrl = title.lower().replace(' ', '_')
        customUrl = re.sub(r'[<>:"/\\|?*]', "", customUrl)
        contentDetails = items[0].get('contentDetails',{})
        if not contentDetails:
            print('There is not contentDetails in the Playlist')
            return
        
        playlist_info = {
            'title': title,
            'customUrl': customUrl,
            'channelId': channelId,
            'channelTitle': title,
            'uploads': playlist_id,
        }
        if print_info:
            align = max(len(k) for k in playlist_info)
            for k, v in playlist_info.items():
                if k == 'uploads':
                    print(f'{k+": ":<{align + 2 }}{yt_playlist}{v}')
                else:
                    print(f'{k+": ":<{align + 2 }}{v}')
                    
                    
        return playlist_info

    def get_added_video_response_info(self, added_response: dict, print_info: bool = False) -> dict | None:
        id_response = added_response.get('id')
        # print(id_response)
        snippet = added_response.get('snippet', {})
        if not snippet:
            print(f'The video ID {id_response} does not have a snippet in the Added response')
            return
        resourceId = snippet.get('resourceId')
        videoId = resourceId.get('videoId')
        title = snippet.get('title')
        videoOwnerChannelTitle = snippet.get('videoOwnerChannelTitle')
        
        contentDetails = added_response.get('contentDetails', {})
        videoPublishedAt = contentDetails.get('videoPublishedAt')      
        response_info = {
            'id_response': id_response,
            'videoPublishedAt': videoPublishedAt,
            'title': title,
            'videoOwnerChannelTitle': videoOwnerChannelTitle,
            'videoId': videoId
        }
        if print_info:
            print_dictionary(response_info)

        return response_info
    
    def is_restricted(self, response: dict) -> None | dict:
        items = response.get('items', [])
        if not items:
            print('There is no items response')
            print(response)
            return
        else: 
            contentDetails = items[0].get('contentDetails', {})
            regionRestriction = contentDetails.get('regionRestriction',{})
            blocked = regionRestriction.get('blocked', [])
            allowed = regionRestriction.get('allowed', [])
            if self.current_country in blocked or (allowed and self.current_country not in allowed):
                return regionRestriction

    def add_response_df(self, file_path: Path, response: dict) -> None:    
        columns_df = ['videoID','title', 'publishedAt', 'restriction']
        if not file_path.exists():
            df = pd.DataFrame(columns = columns_df)
        else:
            df = pd.read_csv(file_path, encoding="utf-8")
    
        items = response.get('items', [])
        if not items:
            print("Response doesn't have have items")
            return
        videoID = items[0].get('id', "")
        if videoID in df['videoID'].values:
            print(f'{videoID} already in the Data Frame {file_path.name}')
            return

        snippet = items[0].get('snippet', {})
        publishedAt = snippet.get('publishedAt', '')
        title = snippet.get('title', '')
        contentDetails = items[0].get('contentDetails', {})
        regionRestriction = contentDetails.get('regionRestriction', {})
        restriction = ""
        if regionRestriction:
            for res, countries in regionRestriction.items():
                restriction += f'{res}: {", ".join(countries)}.'
        new_row_data = [videoID,title, publishedAt, restriction]
        
        df.loc[len(df)] = new_row_data
        df.sort_values(by="publishedAt", ascending=True, inplace=True, ignore_index=True)
        self.files_manager.write_csv_safely(df, file_path)

if __name__ == '__main__':
    from YouTube import YouTubeManager
    rsp_mng = response_manager()

    # yt = YouTubeManager()
    # playlist_id = 'PLCFlKAAOW47g'
    # playlist_response = yt.get_response_from_playlist_id(playlist_id)
    # rsp_mng.get_playlist_info(playlist_response, True)
  

    
