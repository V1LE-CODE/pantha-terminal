from datetime import datetime
import platform
import os

HELP_TEXT = """Available commands:
  help              Show this help message
  clear             Clear the output screen
  about             About Pantha Terminal
  time              Show current time
  system            Show system info
  echo <text>       Print text
  ls                List files in current directory
  pwd               Show current directory
  exit              Quit Pantha Terminal
"""

def run_command(command: str):
    command = command.strip()
    if not command:
        return ("", None)

    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        return (HELP_TEXT, None)

    if cmd == "about":
        return ("Pantha Terminal 💜\nA neon purple aesthetic terminal built with Textual.", None)

    if cmd == "time":
        return (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None)

    if cmd == "system":
        return (
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Machine: {platform.machine()}",
            None
        )

    if cmd == "echo":
        return (" ".join(args), None)

    if cmd == "pwd":
        return (os.getcwd(), None)

    if cmd == "ls":
        try:
            files = os.listdir(".")
            return ("\n".join(files) if files else "(empty)", None)
        except Exception as e:
            return (f"Error: {e}", None)

    if cmd == "clear":
        return ("", "clear")

    if cmd == "exit":
        return ("", "exit")

    return (f"Unknown command: {cmd}\nType 'help' to see commands.", None)
