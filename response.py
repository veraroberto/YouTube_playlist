import isodate, json
import pandas as pd
from filesManager import filesManager
from YouTube import YouTubeManager
from urllib.request import urlopen

class response_manager():
    default_date = "2005-04-24T03:31:52Z" #Timestamp of the first YouTube video ever published 

    def __init__(self):
        self.files_manager = filesManager()
        self.youtube = YouTubeManager()
        self.data = json.load(urlopen('https://ipinfo.io/'))
        self.current_country = self.data.get('country')
        
    def get_video_info(self, response):
        items = response.get('items', [])
        if not items:
            return {}
        video_id = response['items'][0]['id']
        
        snippet = items[0].get('snippet', {})
        publishedAt = snippet.get('publishedAt', self.default_date)  #Timestamp of the first YouTube video ever published 
        title = snippet.get('title', "")
        channelTitle = snippet.get('channelTitle',"")
        
        contentDetails = items[0].get('contentDetails', {})
        regionRestriction = contentDetails.get('regionRestriction',{})
        restriction = regionRestriction.get('blocked', [])
        restriction.extend(regionRestriction.get('allowed', []))
        duration_iso = contentDetails.get('duration', 'PT0S')
        duration = isodate.parse_duration(duration_iso).total_seconds()
        liveBroadcastContent = snippet.get('liveBroadcastContent', None)
        liveStreamingDetails = items[0].get('liveStreamingDetails', None)
        video_id_info = {'video_id': video_id,
                         'channelTitle': channelTitle,
                         'publishedAt': publishedAt,
                         'title': title,
                         'duration' : duration,
                         'liveBroadcastContent': liveBroadcastContent,
                         'liveStreamingDetails': liveStreamingDetails,
                         'regionRestriction':restriction
                        }
        return video_id_info

    def is_restricted(self, response):
        items = response.get('items', [])
        if not items:
            print('There is no items response')
            return
        else: 
            contentDetails = items[0].get('contentDetails', {})
            regionRestriction = contentDetails.get('regionRestriction',{})
            blocked = regionRestriction.get('blocked', [])
            allowed = regionRestriction.get('allowed', [])
            if self.current_country in blocked or (allowed and self.current_country not in allowed):
                return regionRestriction

    def add_response_df(self, file_path, response):    
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
    response_mng = response_manager()
 