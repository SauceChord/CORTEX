import subprocess
import os

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

def run_bash(command_line):
    """Run a bash command line on the user's machine"""

    print(f"{GREEN}>{RESET} {command_line}")    
    command_line_expanded = (f"({command_line}) ; pwd")
    result = subprocess.run(['bash', '-c', command_line_expanded], capture_output=True, text=True)

    # Change current working directory since commands might change it (cd ..) etc
    lines = result.stdout.rstrip().splitlines()
    os.chdir(lines[-1] if lines else os.getcwd())

    # Strip out the last line which is the current working directory (if any)
    command_line_output = '\n'.join(lines[:-1]) if lines else ''

    print(command_line_output)
    
    if result.stderr:
        print(f"{RED}{result.stderr}{RESET}")
        
    return result.stderr if result.stderr else command_line_output