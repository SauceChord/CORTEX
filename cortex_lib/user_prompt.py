import os
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import FormattedText
from cortex_lib.config import settings

bindings = KeyBindings()


# Pressing Ctrl + W changes mode between chat and command.
# Default is command, which executes user commands on the shell.
# The other is Chat, which allows Cortex (AI) to read command
# history including output. It can also ask to run commands on
# the users behalf.
@bindings.add(Keys.ControlW)
def switch_to_command_mode(event):
    global promptMode
    promptMode = (
        PromptMode.COMMAND if promptMode == PromptMode.CHAT else PromptMode.CHAT
    )
    session.app.exit()


class PromptMode:
    COMMAND = "command"
    CHAT = "chat"


promptMode = PromptMode.COMMAND


def get_prompt_mode():
    return promptMode


def get_git_branch():
    """
    Returns the current git branch in the current working directory, if any, or an empty string.
    """
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
        ).strip()
        return "" if branch == "" else f"({branch.decode('utf-8')})"
    except Exception:
        return ""


def get_user_prompt():
    """
    Get user prompt with format
    (current-git-branch) path/to/current/working/directory:
    """
    global session
    result = None
    while not result:
        if promptMode == PromptMode.COMMAND:
            file_completer = None if not settings.autocomplete else get_file_completer()
            session = PromptSession(key_bindings=bindings, completer=file_completer)
            formatted_text = FormattedText(
                [
                    ("fg:yellow", "RUN"),
                    ("fg:green", " "),
                    ("fg:green", get_git_branch()),
                    ("fg:green", " "),
                    ("fg:gray", os.getcwd()),
                    ("fg:green", "> "),
                ]
            )
            result = session.prompt(formatted_text)
        elif promptMode == PromptMode.CHAT:
            session = PromptSession(key_bindings=bindings)
            formatted_text = FormattedText(
                [
                    ("fg:yellow", "CHAT"),
                    ("fg:green", " "),
                    ("fg:green", get_git_branch()),
                    ("fg:green", " "),
                    ("fg:gray", os.getcwd()),
                    ("fg:green", "> "),
                ]
            )
            result = session.prompt(formatted_text)
    return result


def get_file_completer():
    files = []
    for dirpath, dirnames, filenames in os.walk(
        "."
    ):  # Walk through the current directory
        for filename in filenames:
            files.append(
                os.path.relpath(os.path.join(dirpath, filename), os.getcwd())
            )  # Add relative paths
    file_completer = WordCompleter(files, ignore_case=True)
    return file_completer
