from pathlib import Path

content_creator_folder = Path('Content Creators')
content_creator_folder_response = Path('Content Creators Response')
exception_folder = Path('Exceptions')
playlist_folder =  Path("Playlists")
restriction_folder = Path('Restrictions')
stats_folder = Path('Stats')
tokens_folder = Path("Tokens")
html_folder = Path('HTML')


if not content_creator_folder.exists():
    content_creator_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {content_creator_folder.stem} was created')

if not content_creator_folder_response.exists():
    content_creator_folder_response.mkdir(parents=True, exist_ok=True)
    print(f'The folder {content_creator_folder_response.stem} was created')

if not exception_folder.exists():
    exception_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {exception_folder.stem} was created')

if not playlist_folder.exists():
    playlist_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {playlist_folder.stem} was created')

if not restriction_folder.exists():
    restriction_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {restriction_folder.stem} was created')

if not stats_folder.exists():
    stats_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {stats_folder.stem} was created')

if not tokens_folder.exists():
    tokens_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {tokens_folder.stem} was created')

if not html_folder.exists():
    html_folder.mkdir(parents=True, exist_ok=True)
    print(f'The folder {html_folder.stem} was created')        

# watch_later_id_path = stats_folder / "watch_later_id.py"
# if not watch_later_id_path.exists():
#     content = "watch_later_id = ''"
#     watch_later_id_path.write_text(content)
#     print(f'The file {watch_later_id_path} was created. Check the file for more details')
# else:
#     from watch_later_id_path



columns_df = ['Handle', 'channelTitle', 'channelId', 'uploads']

yt_url = 'https://www.youtube.com/watch?v='
yt_playlist = 'https://www.youtube.com/playlist?list='
yt_channel = 'https://www.youtube.com/channel/'