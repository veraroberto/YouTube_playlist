import unicodedata
import os
import requests
from bs4 import BeautifulSoup
# from urllib.parse import urlparse, parse_qs
from pathlib import Path
from YouTube import yt_url

def clear_terminal() -> None:
    # Check operating system and use the appropriate command
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def generate_lable(options: list) -> dict:
        option_map = {}
        for i, value in enumerate(options, 1):
            label = ""
            n = i
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                label = chr(65 + remainder) + label
            
            option_map[label] = value
            print(f"[{label}] {value}")
        return option_map

def choose_option(options: list, message: str = "Enter your choice: ") -> str | None:
    if not isinstance(options, list):
        raise TypeError(f"Expected a list, but got {type(options).__name__}")
    
    if not options:
        return None

    # 1. Create the mapping using the math helper
    print(f'{message}')
    option_map = generate_lable(options)
  
    while True:
        choice = input("Select an option: ").strip().upper()
        if not choice: # Handle empty Enter key
            continue
        if choice in option_map:
            return option_map[choice]
        print(f"Invalid choice '{choice}'. Please pick a label from the list.")

def remove_accents(text: str) -> str:
    # Normalize the text to separate base letters and diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Filter out the diacritic marks
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents

def duration_string(duration: float | int) -> str:
    #Duration in seconds
    if isinstance(duration, (float, int)):
        hrs, mins = divmod(duration, 3600)
        mins, secs = divmod(mins, 60)
        duration_string = f'{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}'
        return duration_string
    else:
        print(f'{duration} is not a number')

def is_short(video_id: str) -> bool | None:
    url = f'https://www.youtube.com/shorts/{video_id}'
    response = requests.get(url, allow_redirects=True)
    if response.status_code == 429:
        print("Too many requests — you've hit a rate limit.")
        return 
    elif response.status_code == 403:
        print("Access forbidden — you may be blocked.")
        return 
    
    # The final URL after redirects
    final_url = response.url

    # If it redirects to the watch URL, it's not a Short
    if 'youtube.com/watch?v=' in final_url:
        return False
    elif 'youtube.com/shorts/' in final_url:
        return True
    else:
        return  # Unexpected case

def create_bookmarks_2(urls: dict,file_path: Path="bookmarks.html"):
    with open(file_path, mode="r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')
    print(soup)

    all_a = soup.find_all("a")
    current_urls = [a.get('href') for a in all_a]

    # Firefox bookmark header
    html = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>'
    ]

    for p in urls:
        html.append(f'    <DT><A HREF="{yt_url+ p}">{urls[p]}</A>')

    html.append('</DL><p>')

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print(f"🔥 bookmarks created: {file_path}")

import os
from bs4 import BeautifulSoup

def create_bookmarks(file_path: Path, link_dict: dict):
# 1. Check if file exists AND has content; otherwise, create a skeleton
    if not file_path.exists(): #or os.stat(file_path).st_size == 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("<html><body><div id='link-container'></div></body></html>")

    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 2. Safety Check: Ensure container or body exists
    container = soup.find(id='link-container')
    if container is None:
        # If no container, use body; if no body, create one
        container = soup.body if soup.body else soup.new_tag("body")
        if not soup.body:
            soup.append(container)

    # 3. Extract existing URLs
    existing_links = {a.get('href') for a in container.find_all('a') if a.get('href')}

    # 4. Add missing links
    for partial_path, title in link_dict.items():
        # Cleanly join base and partial URL
        full_url = f"{yt_url.rstrip('/')}/{partial_path.lstrip('/')}"
        
        if full_url not in existing_links:
            new_tag = soup.new_tag("a", href=full_url)
            new_tag.string = title
            container.append(new_tag)

    # 5. Extract, Sort, and Re-insert
    all_a_tags = container.find_all('a')
    # Sort by the link text (Title)
    sorted_tags = sorted(all_a_tags, key=lambda x: (x.text or "").strip().lower(), reverse=True)

    # Clear container and re-add sorted links
    container.clear()
    for tag in sorted_tags:
        container.append(tag)
        container.append(soup.new_tag("br"))

    # 6. Save changes
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

if __name__ == '__main__':
    #
    urls = {}
    file_path = Path('jalasuefitness.html')
    create_bookmarks(file_path, urls)