import os
import shutil
import configparser
import instructor
from dotenv import load_dotenv
from groq import Groq
from gen.run_powershell import run_powershell
from typing import Optional, List
from pydantic import BaseModel, Field

load_dotenv()
config = configparser.ConfigParser()
config.read('config.ini')
history_size = config.getint('Settings', 'history_size')
shell = config.get('Settings', 'shell')
model = config.get('Settings', 'model')

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client = instructor.from_groq(client)

class Response(BaseModel):
    message: str = Field(
        ..., 
        description="The response message or command line explanation"
    )
    command_lines: Optional[List[str]] = Field(
        None, 
        description=f"A sequence of {shell} commands to execute if you deem they should be run"
    )
    

import instructor
from pydantic import BaseModel


def make_instructions(shell):
    return [
        {"role": "system", "content": f"""
         You are a helpful shell AI assistant called Cortex.
         You can run {shell} command lines on the users computer.
         Before performing destructive operations, ask the user for permission before proceeding.
         The users terminal is {shutil.get_terminal_size().columns} characters wide (useful for breaking up long text into readable format).
         Your responses must NOT use markdown. Use plaintext. Use terminal color codes where appropriate for drawing the users attention.         
         When you receive a command line response, use the output to format an answer to the orginal user question, informing them of anything noteworthy.
         """}
    ]

instructions = make_instructions(shell)
chat_history = []

RED = '\033[31m'   # Red color
GREEN = '\033[32m' # Green color
RESET = '\033[0m'  # Reset to default color

def cortex_step():
    print("Type 'exit' to end the session.")
    
    while True:
        global chat_history

        prompt = input(f"{GREEN}{os.getcwd()}: {RESET}")

        if prompt.lower() == "exit":
            print(f"{GREEN}CORTEX:{RESET} Bye!")
            break
    
        chat_history.append({"role": "user", "content": prompt})

        try:
            response = get_response()
            show_message(response)
            run_command_line(response)

        except Exception as e:
            print(f"{RED}Error:{RESET} {e}")

def get_response():
    return client.chat.completions.create(
        model = model,
        messages = instructions + chat_history,
        response_model = Response,
    )    

def show_message(response):
    global chat_history
    global history_size

    if (response.message):
        print(f"{GREEN}CORTEX:{RESET} {response.message}")
        chat_history.append({"role": "assistant", "content": response.message})

    if len(chat_history) > history_size:
        chat_history = chat_history[-history_size:]

def run_command_line(response):
    global chat_history

    if response.command_lines == None:
        return

    for command_line in response.command_lines:
        output = run_powershell(command_line)
        chat_history.append({"role": "user", "content": f"Executed `{command_line}` with output:\n\n{output}"})

if __name__ == "__main__":
    cortex_step()