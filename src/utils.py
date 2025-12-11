import contextlib
import os
import sys

from .config import Colors


@contextlib.contextmanager
def suppress_stdout_stderr():
    """Silencia o erro de biblioteca."""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def print_styled(text):
    """Imprime Markdown com cores no terminal."""
    if not text:
        return

    for line in text.split("\n"):
        if line.strip().startswith("# "):
            print(f"{Colors.HEADER}{Colors.BOLD}{line}{Colors.ENDC}")
        elif line.strip().startswith("## "):
            print(f"\n{Colors.CYAN}{Colors.BOLD}{line}{Colors.ENDC}")
        elif line.strip().startswith("### "):
            print(f"{Colors.BLUE}{Colors.BOLD}{line}{Colors.ENDC}")
        elif "**" in line:
            # Destaca negritos simples
            parts = line.split("**")
            new_line = ""
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    new_line += f"{Colors.BOLD}{part}{Colors.ENDC}"
                else:
                    new_line += part
            print(new_line)
        else:
            print(line)
