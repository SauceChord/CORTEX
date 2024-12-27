import os
import shutil
import instructor
from dotenv import load_dotenv
from openai import OpenAI
from cortex_lib.shell import run_ps, run_bash
from cortex_lib.config import settings
from cortex_lib.responses import RequestResponse, ResultResponse
import subprocess

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = instructor.from_openai(client)
history = []

shell = {
    "powershell": run_ps,
    "bash": run_bash,
}

instructions = [{"role": "system", "content": f"""
You are a helpful and intelligent shell assistant named Cortex, designed to assist with running command-line tasks on the user's computer.

Your role is to interpret and execute commands carefully. You should ensure that commands are valid and safe to run in the terminal, avoiding any harmful operations. Always verify that the command makes sense before executing it. If you're unsure, ask the user for clarification rather than making assumptions.

Your responses should:
1. Be in plaintext format. Do not use markdown, HTML, or any formatting that could confuse the user.
2. Avoid long, unbroken lines of text. If necessary, break text into multiple lines for readability, especially when the terminal window is narrow (approximately {shutil.get_terminal_size().columns / 2} characters wide).
3. Use terminal color codes for visual emphasis, especially when drawing the user's attention to important information or errors. For example, use green for success, red for errors, and yellow for warnings or informative messages.
4. Include helpful messages that explain any actions taken or errors encountered.
5. Ensure that all commands run in the {settings.shell} shell. Avoid mixing shell commands or assuming an incorrect environment.
6. If the output is too long, split it into manageable chunks that fit within the terminal width, and prompt the user to request the next part if necessary.
7. Always check the user's request for typos or ambiguous instructions, and ask for clarification if needed before proceeding.
8. When a user seems to ask a short hand notation for a command to be executed but isn't ambigious, execute it if it is safe.

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
    
def cortex_step(history):
    # Obtain user prompt
    prompt = input(f"{get_git_branch()} {GREEN}{os.getcwd()}: {RESET}")
    if prompt.lower().strip() == "exit":
        print(f"{GREEN}CORTEX:{RESET} Bye!")
        return False
    history.append({"role": "user", "content": prompt})
    try:
        # Process the users request
        response = get_response(history, RequestResponse)
        show_message(history, response)
        run_commands(history, response)
    except Exception as e:
        print(f"{RED}Error:{RESET} {e}")
    return True

def get_response(history, response_model):
    return client.chat.completions.create(
        model = settings.model,
        messages = instructions + history,
        response_model = response_model,
    )    

def show_message(history, response):
    if (response.message):
        print(f"{GREEN}CORTEX:{RESET} {response.message}")
        history.append({"role": "assistant", "content": response.message})
    if len(history) > settings.history_size:
        history = history[-settings.history_size:]

def run_commands(history, response):
    if response.command_lines == None:
        return
    for command_line in response.command_lines:
        output = shell[settings.shell](command_line)
        history.append({"role": "user", "content": f"Executed `{command_line}` with output:\n\n{output}"})
        # Explain what happened
        response = get_response(history, ResultResponse)
        show_message(history, response)        


if __name__ == "__main__":
    print(f"{GREEN}CORTEX:{RESET} Type {GREEN}exit{RESET} to end the session!")
    while cortex_step(history):
        pass