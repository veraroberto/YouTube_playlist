from pathlib import Path
import shutil, time, re, unicodedata, json, pyperclip
from mutagen.mp4 import MP4
from IPython.display import clear_output
from datetime import datetime, date as dt_date, timedelta
from IPython.display import clear_output
tv_folder = Path('/Volumes/ROBERTO/TV')
tv_folder.exists()
models = tv_folder / 'Models'
home_videos = tv_folder / 'Home Videos'


extensions = ['.mp4', '.mov', '.m4v']
list_comments = ['NABLOG', 'XXXClub.to', 'NAUGHTYBLOG']


def duration_string(duration):
    #Duration in seconds
    if isinstance(duration, (float, int)):
        hrs, mins = divmod(duration, 3600)
        mins, secs = divmod(mins, 60)
        duration_string = f'{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}'
        return duration_string
    else:
        print(f'{duration} is not a number')

def get_elements_from_file(file_path):
    file_path = file_path.with_suffix('.txt')
    file_path.touch()
    elements = file_path.read_text().splitlines()
    return elements


def add_list_to_file(file_path, list_elements, sort_list = True):
    file_path = file_path.with_suffix('.txt')
    elements_file = get_elements_from_file(file_path)
    for e in list_elements:
        if e not in elements_file:
            elements_file.append(e)
    if sort_list:
        elements_file.sort(key= str.lower)
    file_path.write_text('\n'.join(map(str, elements_file)))
    return elements_file

def add_element_to_file(file_path, element, sort_list = True, print_statement = False):
    file_path = file_path.with_suffix('.txt')
    elements = get_elements_from_file(file_path)
    if element not in elements:
        elements.insert(0,element)
    else:
        if print_statement:
            print(f'{element} is already in {file_path.name}')
    if sort_list:
        elements.sort(key= str.lower)
    add_list_to_file(file_path, elements, sort_list)
    return elements

def remove_accents(text: str) -> str:
    # Normalize the text to separate base letters and diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Filter out the diacritic marks
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents


list_substrings = ['1080p', 'MP4-NABL0G','MP4-COCKiNE','MP4-WRB','WEBRip', '720p', '1440p','2160p','1280p', 'MP4-NABLOG', 'sd', 'dvdrip', 'x264-cic', 'MP4-NBQ', 'MP4-Narcos', 'NAUGHTYBLOG']
list_substrings = [s.lower() for s in list_substrings]
dict_formated = {'ftvmilfs': 'FTVMilfs',
              'sexart': 'SexArt',
                'sart': 'SexArt'}


def remove_substrings(text, list_substrings, dict_formated):
    #remove Collectio_

    idx = text.find('Collection_')
    if idx != -1:  # substring found
        text =  text[idx + len('Collection_'):]  # cut before + including substring
    text_splited = [t for t in re.split(r'[ .\s]+', text) if t]
    new_text_list = []
    for word in text_splited:
        if word.lower() in dict_formated.keys():
            new_text_list.append(dict_formated[word.lower()])
        # elif word.lower() not in list_substrings:
        elif not any(s in word.lower() for s in  list_substrings):
            if word[0].isupper():
                new_text_list.append(word)
            else:
                new_text_list.append(word.title())
    new_text = ".".join(new_text_list)   
    new_text = re.sub(r'#\S*', '', new_text) #Remove #Hashtags   
    
    if new_text[-3:].lower() == 'xxx':
        new_text = new_text[0:-3]
    return new_text.strip(' .')           
    


def move_date_to_start(text):

    match = re.search(r'\b\d{2}\.\d{2}\.\d{2}.\b', text)
    if match:
        date_part = match.group(0)                # the matched dd.dd.dd
        rest = text.replace(date_part, "", 1).strip()  # remove first occurrence
        return f"20{date_part}{rest}"
    else:
        return text  # return unchanged if no match

def clean_metadata(text, list_substrings, dict_formated):
    text = new_name = remove_substrings(text, list_substrings, dict_formated)       
    text = move_date_to_start(new_name)
    return text

def write_date_numbers(date_string):

    date_pattern = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),?\s*(\d{4})?"
    match =  re.search(date_pattern, date_string.lower())
    if match:
        date_string = match.group(0)
        year_str = match.group(3)
        if not year_str:
            year = dt_date.today().year
            date_string = f'{date_string}, {year}'
        
        date_object = datetime.strptime(date_string, '%b %d, %Y')
        formatted_date = date_object.strftime('%Y.%m.%d.')
    elif 'today' in date_string.lower() or 'ago' in date_string.lower():
        formatted_date = dt_date.today().strftime('%Y.%m.%d.')    
        
    elif 'yesterday' in date_string.lower():
        yesterday = dt_date.today() - timedelta(days=1)
        formatted_date = yesterday.strftime('%Y.%m.%d.')

    else:
        return date_string
    return formatted_date