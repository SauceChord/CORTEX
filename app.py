# Standard library
import os
import subprocess
import threading
import time

# Settings
from dotenv import load_dotenv

# AI
from openai import OpenAI
import instructor

# Console
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import FormattedText

# Helpers
from cortex_lib.shell import run_ps, run_bash
from cortex_lib.config import settings
from cortex_lib.responses import RequestResponse, ResultResponse

# .env file should have OPENAI_API_KEY defined, unless set as OS environment variable
load_dotenv()
client = OpenAI(api_key = os.environ.get("OPENAI_API_KEY"))
client = instructor.from_openai(client)

history = []
console = Console()
is_waiting_for_cortex = False

class PromptMode:
    COMMAND = 'command'
    CHAT = 'chat'

promptMode = PromptMode.COMMAND

bindings = KeyBindings()

# Pressing Ctrl + W changes mode between chat and command. 
# Default is command.
@bindings.add(Keys.ControlW)
def switch_to_command_mode(event):
    global promptMode
    promptMode = PromptMode.COMMAND if promptMode == PromptMode.CHAT else PromptMode.CHAT
    session.app.exit()

# Supported shells, configured in config.ini
shell = {
    "powershell": run_ps,
    "bash": run_bash,
}

# AI's instructions to adhere to. Always sent to the AI.
instructions = [{"role": "system", "content": f"""
You are a helpful and intelligent shell assistant named Cortex, designed to assist with running command-line tasks on the user's computer.

Your role is to interpret and execute commands carefully and efficiently. You should ensure that commands are valid and safe to run in the terminal, avoiding any harmful operations. Always verify that the command makes
sense before executing it. If you're unsure, ask the user for clarification rather than making assumptions.

Your responses should:

 1 Include helpful messages that explain any actions taken or errors encountered.
 2 Ensure that all commands run in the appropriate shell environment.
 3 Always check the user's request for typos or ambiguous instructions, and seek clarification if needed before proceeding.
 4 Execute commands directly without asking for permission unless a command is particularly sensitive or may cause harm.
 5 Maintain a clear and concise communication style, ensuring the user understands all actions and results clearly.

You are here to make the user's terminal experience smoother and more efficient. Keep responses clear, concise, and supportive."""}]

# Helpers for coloring terminal output
RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

def get_git_branch():
    """
        Returns the current git branch in the current working directory, if any, or an empty string.
    """
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).strip()
        return "" if branch == "" else f"({branch.decode('utf-8')})"
    except Exception:
        return ''
    
def talk_to_ai(history, message_to_cortex):
    """
        Given a history and a user prompt, talk to the AI.
        The AI will respond with a message that may include
        running one or several command lines for the current 
        shell.
    """
    try:
        history.append({"role": "user", "content": message_to_cortex})
        response = cortex_response(history, RequestResponse)
        cortex_says(history, response.message)
        cortex_executes(history, response.command_lines)
    except Exception as e:
        print(f"{RED}Error:{RESET} {e}")

def run_command(history, command):
    """
        Runs a command and optionally has the AI explain
        the results of it, if configured in config.ini.

        The AI remembers for a moment the executed command
        and the command result, so the user can chat to
        it about it.
    """
    try:
        output = shell[settings.shell](command)
        history.append({"role": "user", "content": f"Executed command: {command}\nOutput: {output}"})
        if (settings.explain):
            response = cortex_response(history, ResultResponse)
            cortex_says(history, response.message)
    except Exception as e:
        print(f"{RED}Error occured during command execution:{RESET} {e}")

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
            formatted_text = FormattedText([
                ('fg:yellow', "RUN"),
                ('fg:green', " "),
                ('fg:green', get_git_branch()),
                ('fg:green', " "),
                ('fg:gray', os.getcwd()),
                ('fg:green', ">"),
            ])
            result = session.prompt(formatted_text)
        elif promptMode == PromptMode.CHAT:
            session = PromptSession(key_bindings=bindings)
            formatted_text = FormattedText([
                ('fg:yellow', "CHAT"),
                ('fg:green', " "),
                ('fg:green', get_git_branch()),
                ('fg:green', " "),
                ('fg:gray', os.getcwd()),
                ('fg:green', ">"),
            ])
            result = session.prompt(formatted_text)
    return result

def get_file_completer():
    files = []
    for dirpath, dirnames, filenames in os.walk('.'):  # Walk through the current directory
        for filename in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, filename), os.getcwd())) # Add relative paths
    file_completer = WordCompleter(files, ignore_case=True)
    return file_completer

def cortex_step(history):
    """
        Get a user prompt and either
        - Exit
        - Talk to the AI (start prompt with ")
        - Run a command
    """
    prompt = get_user_prompt()
        

    # Allow users to exit
    if prompt.lower().strip() == "exit":
        print(f"{GREEN}CORTEX:{RESET} Bye!")
        return False

    # " means to talk with AI, otherwise, run command.
    if promptMode == PromptMode.CHAT:
        talk_to_ai(history, prompt)
    elif promptMode == PromptMode.COMMAND:
        run_command(history, prompt)

    return True

def cortex_waiting():
    """
        Displays a loading cursor while processing commands.
    """
    console.show_cursor(False)
    with console.status("") as status:
        status.start()
        while is_waiting_for_cortex:
            time.sleep(0.05)
        status.stop()
    console.show_cursor(True)


def cortex_response(history, response_model):
    """
        Sends instructions and chat history to the AI model
        with a response model to fill in details.
        
        While waiting for a response, a spinner is shown.
    """
    global is_waiting_for_cortex
    is_waiting_for_cortex = True
    waiting_thread = threading.Thread(target=cortex_waiting)
    waiting_thread.start()    
    try:
        result = client.chat.completions.create(
            model = settings.model,
            messages = instructions + history,
            response_model = response_model,
        )
    finally:
        is_waiting_for_cortex = False
        waiting_thread.join()
    return result

def cortex_says(history, message):
    """
        Called when CORTEX says something.
        - Printed to screen
        - Appended to history
        - History trimmed (to avoid usage costs) - size configurable in config.ini
    """
    if (message):
        markdown = Markdown(f"{GREEN}CORTEX:{RESET} {message}")
        console.print(markdown)
        history.append({"role": "assistant", "content": message})
    if len(history) > settings.history_size:
        history = history[-settings.history_size:]

def cortex_executes(history, command_lines):
    """
        Given a list of command lines cortex wants to run,
        Present the suggested commands to the user
        Ask the user for permission to run the commands
    """
    if command_lines == None:
        return
    
    # Print a list of commands that cortex wants to run
    print('\n'.join(command_lines))

    count = len(command_lines)
    plural = "s" if count > 1 else ""

    # Wait for the user to approve or deny execution
    while True:
        choice = input(f"Do you want to run these command{plural}? ({GREEN}yes{RESET}/{GREEN}no{RESET}): ").strip().lower()
        if choice == "n" or choice == "no":
            history.append({"role": "user", "content": f"I've declined running your suggestion{plural}."})
            if (settings.explain):
                response = cortex_response(history, ResultResponse)
                cortex_says(history, response.message)        
            return
        if choice == "y" or choice == "yes":
            break

    # Run all commands.
    for command in command_lines:        
        run_command(history, command)

if __name__ == "__main__":
    """
        This is the entry point of the program. 
        It keeps looping through cortex_step
    """
    try:            
        cortex_says(history, "Welcome, I am your helpful shell assistant **Cortex**!")
        cortex_says(history, "Type `exit` to end the session!")    
        while cortex_step(history):
            pass
    except KeyboardInterrupt:
        pass