import pyperclip, string, itertools, unicodedata, requests
from urllib.parse import urlparse, parse_qs

def choose_option(options, message="Enter your choice: "):
        
    # 1. Generate Excel-style labels (A, B... Z, AA, AB...)
    def get_labels(count):
        labels = []
        n = 1
        while len(labels) < count:
            # Generate combinations of length n ('A', then 'AA', then 'AAA')
            for combo in itertools.product(string.ascii_uppercase, repeat=n):
                labels.append("".join(combo))
                if len(labels) == count:
                    break
            n += 1
        return labels

    # 2. Map labels to options
    option_labels = get_labels(len(options))
    option_map = dict(zip(option_labels, options))

    while True:
        print(message.strip())
        for letter, option in option_map.items():
            print(f"  {letter}) {option}")
        choice = input("Enter your choice: ").strip().upper()
        # Check for user input or the pyperclip bypass
        if choice in option_map:#pyperclip.paste() == 'choose_option':
            if pyperclip.paste() == 'choose_option':
                print('There was no option chosen and the function was interrupted')
                return None
            
            print(f"  {choice}) {option_map[choice]}")
            return option_map[choice]
        elif choice.lower() == 'exit' or  choice == "":
            print('No option was selected')
            return
        else:

            print("Invalid choice. Please try again.\n")

def remove_accents(text: str) -> str:
    # Normalize the text to separate base letters and diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Filter out the diacritic marks
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents

def duration_string(duration):
    #Duration in seconds
    if isinstance(duration, (float, int)):
        hrs, mins = divmod(duration, 3600)
        mins, secs = divmod(mins, 60)
        duration_string = f'{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}'
        return duration_string
    else:
        print(f'{duration} is not a number')




if __name__ == '__main__':
    




    pass