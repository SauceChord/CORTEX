# Standard library
import os
import threading
import time

# Settings
# .env file should have OPENAI_API_KEY defined, unless set as OS environment variable
from dotenv import load_dotenv

# AI
from openai import OpenAI
import instructor

# Console
from rich.console import Console
from rich.markdown import Markdown

# App functions and classes
from cortex_lib.shell import run_ps, run_bash
from cortex_lib.config import settings_hint, set_settings, get_settings
from cortex_lib.responses import RequestResponse, ResultResponse
from cortex_lib.user_prompt import get_user_prompt, get_prompt_mode, PromptMode

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = instructor.from_openai(client)

# AI's instructions to adhere to. Always sent to the AI.
instructions = [
    {
        "role": "system",
        "content": f"""
You are a highly-capable shell assistant named Cortex, focused on executing   
command-line tasks on the user's computer. Ensure that each response contains 
explicit guidance or executable steps for the user.

When responding to a request, aim to:

 1 Provide precise explanations of potential actions or solutions, and try to include any settings or configurations the user might need to consider or alter.
 2 Populate the settings fields clearly to reflect any changes requested, such as adjustments in shell type, history size, or AI behavior settings.
 3 Present command lines explicitly when relevant, ensuring they match user's requests for execution tasks or inquiries.
 4 Confirm and clarify the user's instructions to avoid any misunderstandings, ensuring the intended task is properly interpreted.
 5 Suggest running necessary command lines or implementing configuration adjustments where applicable, maintaining a focus on safety and relevance. 

Use this enhanced focus to assist the user in executing tasks efficiently,    
ensuring clarity and a seamless workflow.""",
    }
]

console = Console()

history = []
is_waiting_for_cortex = False

# Supported shells, configured in config.ini
shell = {
    "powershell": run_ps,
    "bash": run_bash,
}

# Helpers for coloring terminal output
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def talk_to_cortex(history, message_to_cortex):
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
        cortex_configures(history, response.settings)
        cortex_executes(history, response.command_lines)
    except Exception as e:
        print(f"{RED}Error:{RESET} {e}")


def cortex_configures(history, settingsResponse):
    if not settingsResponse:
        return
    settings = get_settings()
    settings.history_size = (
        settings.history_size
        if settingsResponse.history_size == None
        else settingsResponse.history_size
    )
    settings.shell = (
        settings.shell if settingsResponse.shell == None else settingsResponse.shell
    )
    settings.model = (
        settings.model if settingsResponse.model == None else settingsResponse.model
    )
    settings.explain = (
        settings.explain
        if settingsResponse.explain == None
        else settingsResponse.explain
    )
    settings.autocomplete = (
        settings.autocomplete
        if settingsResponse.autocomplete == None
        else settingsResponse.autocomplete
    )
    history.append({"role": "user", "content": settings_hint()})
    print(settings_hint())
    set_settings(settings)


def run_command(history, command):
    """
    Runs a command and optionally has the AI explain
    the results of it, if configured in config.ini.

    The AI remembers for a moment the executed command
    and the command result, so the user can chat to
    it about it.
    """
    try:
        output = shell[get_settings().shell](command)
        history.append(
            {
                "role": "user",
                "content": f"Executed command: {command}\nOutput: {output}",
            }
        )
        if get_settings().explain:
            response = cortex_response(history, ResultResponse)
            cortex_says(history, response.message)
    except Exception as e:
        print(f"{RED}Error occured during command execution:{RESET} {e}")


def cortex_step(history):
    """
    Get a user prompt and either
    - Exit
    - Talk to the AI
    - Run a command
    """
    prompt = get_user_prompt()

    # Allow users to exit
    if prompt.lower().strip() == "exit":
        print(f"{GREEN}CORTEX:{RESET} Bye!")
        return False

    # " means to talk with AI, otherwise, run command.
    if get_prompt_mode() == PromptMode.CHAT:
        talk_to_cortex(history, prompt)
    elif get_prompt_mode() == PromptMode.COMMAND:
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
    current_settings = [{"role": "system", "content": settings_hint()}]
    try:
        result = client.chat.completions.create(
            model=get_settings().model,
            messages=instructions + current_settings + history,
            response_model=response_model,
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
    if message:
        markdown = Markdown(f"{GREEN}CORTEX:{RESET} {message}")
        console.print(markdown)
        history.append({"role": "assistant", "content": message})
    if len(history) > get_settings().history_size:
        history = history[-get_settings().history_size :]


def cortex_executes(history, command_lines):
    """
    Given a list of command lines cortex wants to run,
    Present the suggested commands to the user
    Ask the user for permission to run the commands
    """
    if command_lines == None:
        return

    # Print a list of commands that cortex wants to run
    for command in command_lines:
        print(f"{YELLOW}{command}{RESET}")

    count = len(command_lines)
    plural = "s" if count > 1 else ""

    # Wait for the user to approve or deny execution
    while True:
        choice = (
            input(
                f"Do you want to run above {YELLOW}command{plural}{RESET}? ({GREEN}yes{RESET}/{GREEN}no{RESET}): "
            )
            .strip()
            .lower()
        )
        if choice == "n" or choice == "no":
            history.append(
                {
                    "role": "user",
                    "content": f"I've declined running your suggestion{plural}.",
                }
            )
            if get_settings().explain:
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
        cortex_says(
            history, "Press `Ctrl + W` to toggle between **RUN** and **CHAT** mode."
        )
        cortex_says(history, "Type `exit` to end the session!")
        while cortex_step(history):
            pass
    except KeyboardInterrupt:
        pass
