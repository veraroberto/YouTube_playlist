# colors.py

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    CLEAR_LINE = '\033[K'

    @classmethod
    def format(cls, text: str, *styles: str) -> str:
        """Wraps text with given ANSI styles and appends reset code automatically."""
        style_codes = "".join(styles)
        return f"{style_codes}{text}{cls.RESET}"

# Convenience shortcut functions
def red(text: str) -> str:
    return Color.format(text, Color.RED)

def green(text: str) -> str:
    return Color.format(text, Color.GREEN)

def bold_green(text: str) -> str:
    return Color.format(text, Color.BOLD, Color.GREEN)

if __name__ == "__main__":
    # Example usage
    print(f"{Color.RED}{Color.BOLD}This is bold red text{Color.RESET}")