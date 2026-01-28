import unicodedata
import os
import requests

from urllib.parse import urlparse, parse_qs


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
    

if __name__ == '__main__':
    op = choose_option([True, False], "Choose:")