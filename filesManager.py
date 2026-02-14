import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo 
from pathlib import Path

from paths import (content_creator_folder,
                   content_creator_folder_response,
                   exception_folder,
                   playlist_folder,
                   restriction_folder,
                   stats_folder,
                   tokens_folder,
                   html_folder,
                   columns_df)

class filesManager:   
    def __init__(self):
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
            
        self.quota_filename = stats_folder / 'Quota.csv'
        self.file_path_yt_creators = stats_folder / 'YT_content_creators.csv'

        if self.file_path_yt_creators.exists():
            self.YT_content_creators = pd.read_csv(self.file_path_yt_creators)
        else:
            self.YT_content_creators = pd.DataFrame(columns=columns_df)          
        
    def write_csv_safely(self, df: pd.DataFrame, filename: Path) -> None:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            df.to_csv(f, index=False, date_format="%Y-%b-%d")

    def add_to_today_quota(self, new_quota: int) -> None:
        pst_time = datetime.now(ZoneInfo("America/Los_Angeles")) #The quoatas counter is restarted every day a midnight in this time zone
        today_str = pst_time.strftime('%Y-%b-%d')
    
        if not self.quota_filename.is_file():
            df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
            df['Quota'] = df['Quota'].astype(int)
            self.write_csv_safely(df, self.quota_filename)
            print(f"The file {self.quota_filename.stem} was created")
            return
        try:
            df = pd.read_csv(self.quota_filename,  encoding="utf-8")
        except Exception:
            df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
            df['Quota'] = df['Quota'].astype(int)
            self.write_csv_safely(df, self.quota_filename)
            return
        if 'Date' not in df.columns or 'Quota' not in df.columns:
            df = pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])
            df['Quota'] = df['Quota'].astype(int)
            self.write_csv_safely(df, self.quota_filename)
            return
    
        # Normalize date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%b-%d')
    
        if today_str in df['Date'].values:
            df.loc[df['Date'] == today_str, 'Quota'] = (
                df.loc[df['Date'] == today_str, 'Quota'].astype(int) + new_quota)
        else:
            df = pd.concat(
                [df, pd.DataFrame([{'Date': today_str, 'Quota': new_quota}])],
                ignore_index=True)
    
        # Ensure 'Quota' column is integer
        df['Quota'] = df['Quota'].astype(int)
        self.write_csv_safely(df, self.quota_filename)

    def get_today_quota(self, print_statement: bool = False) -> int:    
        pst_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        today_str = pst_time.strftime('%Y-%b-%d')
        # If file doesn't exist, create it with headers
        if not self.quota_filename.exists():
            df = pd.DataFrame(columns=['Date', 'Quota'])
            df.to_csv(self.quota_filename, index=False)
            return 0
        try:
            df = pd.read_csv(self.quota_filename,  encoding="utf-8")
        except Exception as e:
            # If the file can't be read for some reason, treat it as empty
            return 0
        if df.empty or 'Date' not in df.columns or 'Quota' not in df.columns:
            return 0
        # Normalize date format
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%b-%d')
        
        # Find row with today's date
        quota_row = df[df['Date'] == today_str]
                
        if not quota_row.empty:
            current_quota = quota_row.iloc[0]['Quota']
            if print_statement:
                print(f'The current quota usage is: {int(current_quota):,}')
            return current_quota
        else:
            print(f'The current quota usage is 0')
            return 0

    def get_elements_from_file(self, file_path: Path, create_file: bool = False):
            file_path = Path(file_path).with_suffix('.txt')
            if not file_path.exists():
                if create_file:
                    file_path.touch(exist_ok=True)
                return []
            else:
                return file_path.read_text(encoding="utf-8").splitlines()
 
    def add_list_to_file(self, file_path: Path, list_elements: list,
                         sort_list: bool =True, create_file=False) -> None:
        file_path = Path(file_path).with_suffix('.txt')
        if not file_path.exists() and not create_file:
            print('File does not exists')
            return
  

        elements_file = self.get_elements_from_file(file_path)
        
        # Track if we actually added anything to avoid unnecessary disk writes
        has_changes = False
        
        for e in list_elements:
            # Ensure we compare strings to strings
            if str(e) not in elements_file:
                elements_file.append(str(e))
                has_changes = True

        if sort_list:
            elements_file.sort(key=str.lower)
            has_changes = True 

        # The core fix: This is now outside the "if sort_list" block
        if has_changes:
            with file_path.open(mode="w", encoding="utf-8", newline="\n") as f:
                f.write('\n'.join(elements_file))
            
        return elements_file

    def add_element_to_file(self, file_path: Path, element: str,
                            sort_list: bool = True, print_statement: bool = False) -> None:
        file_path = Path(file_path).with_suffix('.txt')
        elements = self.get_elements_from_file(file_path)
        
        # Handle the print statement logic here
        if str(element) in elements:
            if print_statement:
                print(f'{element} is already in {file_path.name}')
            return elements # Exit early since nothing needs to be added
        
        # If it's not in the list, use add_list_to_file to save it
        return self.add_list_to_file(file_path, [element], sort_list)

    def find_missing_elements(self, search_list: list) -> list:
        # Convert to a set so we can remove items as we find them
        remaining_to_find = set(search_list)       
        for file_path in content_creator_folder.iterdir():
            if file_path.suffix == '.txt':
                # If we've already found everything, stop reading files
                if not remaining_to_find:
                    break
                try:
                    # Read file and get unique words/elements
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    file_elements = set(content.split())
                    
                    # Remove any elements found in this file from our 'remaining' set
                    # This is an in-place subtraction
                    remaining_to_find -= file_elements
                    
                except Exception as e:
                    print(f"Error reading {file_path.name}: {e}")
    
        # Convert back to list or return as set
        return list(remaining_to_find)




if __name__ == "__main__":
    fm = filesManager()
    df= fm.YT_content_creators
    handles = df['Handle'].values
    print('JannaBreslin'.lower() in handles)


  


