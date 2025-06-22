import os


def clear_shell():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
