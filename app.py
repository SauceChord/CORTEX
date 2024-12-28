import os
import shutil
import instructor
from dotenv import load_dotenv
from openai import OpenAI
from cortex_lib.shell import run_ps, run_bash
from cortex_lib.config import settings
from cortex_lib.responses import RequestResponse, ResultResponse
import subprocess
from rich.console import Console
from rich.markdown import Markdown
import threading
import time

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = instructor.from_openai(client)
history = []
console = Console()

is_loading = False

def loading():
    console.show_cursor(False)
    with console.status("") as status:
        status.start()
        while is_loading:
            time.sleep(0.05)
        status.stop()
    console.show_cursor(True)

shell = {
    "powershell": run_ps,
    "bash": run_bash,
}

instructions = [{"role": "system", "content": f"""
You are a helpful and intelligent shell assistant named Cortex, designed to assist with running command-line tasks on the user's computer.

Your role is to interpret and execute commands carefully. You should ensure that commands are valid and safe to run in the terminal, avoiding any harmful operations. Always verify that the command makes sense before executing it. If you're unsure, ask the user for clarification rather than making assumptions.

Your responses should:
1. Include helpful messages that explain any actions taken or errors encountered.
2. Ensure that all commands run in the {settings.shell} shell. Avoid mixing shell commands or assuming an incorrect environment.
3. If the output is too long, split it into manageable chunks that fit within the terminal width, and prompt the user to request the next part if necessary.
4. Always check the user's request for typos or ambiguous instructions, and ask for clarification if needed before proceeding.
5. When a user seems to ask a short hand notation for a command to be executed but isn't ambigious, execute it if it is safe.
6. If you feel you need permission from user to run a command, don't include the command in the command_lines reponse.
7. When you respond that you are about to run a command, make sure to include that command in command_lines reponse.

You are here to make the user's terminal experience smoother and more efficient. Keep responses clear, concise, and supportive.
"""}]

RED = '\033[31m'   # Red color
GREEN = '\033[32m' # Green color
RESET = '\033[0m'  # Reset to default color

def get_git_branch():
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).strip()
        if branch == "":
            return ""
        return f"({branch.decode('utf-8')})"
    except Exception:
        return ''
    
def talk_to_ai(history, prompt):
    try:
        history.append({"role": "user", "content": prompt})
        response = get_response(history, RequestResponse)
        show_message(history, response)
        run_commands(history, response)
    except Exception as e:
        print(f"{RED}Error:{RESET} {e}")

def run_command(history, prompt):
    try:
        output = shell[settings.shell](prompt)
        history.append({"role": "user", "content": f"Executed command: {prompt}\nOutput: {output}"})
        if (settings.explain):
            response = get_response(history, ResultResponse)
            show_message(history, response)        
    except Exception as e:
        print(f"{RED}Error:{RESET} {e}")

def cortex_step(history):
    # Obtain user prompt
    prompt = input(f"{get_git_branch()} {GREEN}{os.getcwd()}: {RESET}")
    if prompt.lower().strip() == "exit":
        print(f"{GREEN}CORTEX:{RESET} Bye!")
        return False
    # " means to talk with AI, otherwise, run command.
    if prompt.startswith('"'):
        talk_to_ai(history, prompt[1:].strip())
    else:
        run_command(history, prompt)
    return True

def get_response(history, response_model):
    global is_loading
    is_loading = True
    loading_thread = threading.Thread(target=loading)
    loading_thread.start()    
    try:
        result = client.chat.completions.create(
            model = settings.model,
            messages = instructions + history,
            response_model = response_model,
        )
    finally:
        is_loading = False
        loading_thread.join()
    return result

def show_message(history, response):
    if (response.message):
        markdown = Markdown(f"{GREEN}CORTEX:{RESET} {response.message}")
        console.print(markdown)
        history.append({"role": "assistant", "content": response.message})
    if len(history) > settings.history_size:
        history = history[-settings.history_size:]

def run_commands(history, response):
    if response.command_lines == None:
        return
    for prompt in response.command_lines:
        run_command(history, prompt)

if __name__ == "__main__":
    print(f"{GREEN}CORTEX:{RESET} Type {GREEN}exit{RESET} to end the session!")
    while cortex_step(history):
        pass