from datetime import datetime
import platform
import os
import shutil

HELP_TEXT = """[bold]Available commands:[/]

  help                Show this help message
  clear               Clear the output screen
  exit | quit         Quit Pantha Terminal

  about               About Pantha Terminal
  time                Show current time
  system              Show system info

  echo <text>         Print text
  pwd                 Show current directory
  ls [path]           List files
  cd <path>           Change directory
  whoami              Show current user
  env                 Show environment info
"""

# ------------------------------------
# COMMAND DISPATCH
# ------------------------------------

def run_command(command: str):
    command = command.strip()
    if not command:
        return ("", None)

    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]

    # -------------------------------
    # CORE
    # -------------------------------

    if cmd in ("help", "?"):
        return (HELP_TEXT, None)

    if cmd in ("exit", "quit"):
        return ("", "exit")

    if cmd == "clear":
        return ("", "clear")

    # -------------------------------
    # INFO
    # -------------------------------

    if cmd == "about":
        return (
            "[bold #b066ff]Pantha Terminal[/]\n"
            "A neon-purple terminal built with [bold]Textual[/]\n"
            "Designed for speed, clarity, and power.",
            None,
        )

    if cmd == "time":
        return (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None)

    if cmd == "system":
        return (
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Machine: {platform.machine()}",
            None,
        )

    if cmd == "whoami":
        return (os.environ.get("USERNAME") or os.environ.get("USER") or "pantha", None)

    if cmd == "env":
        return (
            f"Shell: {os.environ.get('SHELL', 'windows')}\n"
            f"Home: {os.path.expanduser('~')}",
            None,
        )

    # -------------------------------
    # FILESYSTEM
    # -------------------------------

    if cmd == "pwd":
        return (os.getcwd(), None)

    if cmd == "cd":
        if not args:
            return (os.path.expanduser("~"), "cd")

        path = os.path.expanduser(args[0])
        try:
            os.chdir(path)
            return (os.getcwd(), None)
        except Exception as e:
            return (f"Error: {e}", None)

    if cmd == "ls":
        path = args[0] if args else "."
        try:
            files = os.listdir(path)
            if not files:
                return ("(empty)", None)

            return ("\n".join(sorted(files)), None)
        except Exception as e:
            return (f"Error: {e}", None)

    # -------------------------------
    # UTIL
    # -------------------------------

    if cmd == "echo":
        return (" ".join(args), None)

    if cmd == "which":
        if not args:
            return ("Usage: which <command>", None)

        result = shutil.which(args[0])
        return (result or "Not found", None)

    # -------------------------------
    # UNKNOWN
    # -------------------------------

    return (
        f"[red]Unknown command:[/] {cmd}\n"
        "Type [bold]help[/] to see available commands.",
        None,
    )
