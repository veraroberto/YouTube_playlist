import unicodedata
from urllib.parse import urlparse, parse_qs


def choose_option(options: list, message: str = "Enter your choice: ") -> str | None:
    if not isinstance(options, list):
        raise TypeError(f"Expected a list, but got {type(options).__name__}")
    
    if not options:
        return None

    # 1. Create the mapping using the math helper
    option_map = {}
    for i, value in enumerate(options, 1):
            label = ""
            n = i
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                label = chr(65 + remainder) + label
            
            option_map[label] = value
            print(f"[{label}] {value}")

    # 2. Input Loop
    while True:
        choice = input(message).strip().upper()
        
        if not choice: # Handle empty Enter key
            continue
            
        if choice in option_map:
            return option_map[choice]
            
        print(f"Invalid choice '{choice}'. Please pick a label from the list.")

# def choose_option(options: list, message: str = "Enter your choice: ") -> str | None:
#     # PEP 8: Type check is good, but removed unreachable return
#     if not isinstance(options, list):
#         raise TypeError(f"Expected a list, but got {type(options).__name__}")
    
#     if not options:
#         return None

#     # Efficient Label Generation using a generator expression
#     # This avoids creating a massive list in memory
#     def generate_labels(count):
#         n = 1
#         found = 0
#         while found < count:
#             for combo in itertools.product(string.ascii_uppercase, repeat=n):
#                 yield "".join(combo)
#                 found += 1
#                 if found == count:
#                     return
#             n += 1

#     # Map labels to options using a dictionary comprehension
#     option_map = dict(zip(generate_labels(len(options)), options))

#     # Display options
#     for label, value in option_map.items():
#         print(f"[{label}] {value}")

#     while True:
#         choice = input(message).strip().upper()
#         if choice in option_map:
#             return option_map[choice]
#         if choice == "EXIT": # Example exit condition
#             return None
#         print("Invalid choice. Please try again.")

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
    options = list(range(1,30))
    print(ord('A'))


    pass