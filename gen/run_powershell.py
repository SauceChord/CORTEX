import subprocess
import os

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

def run_powershell(command_line):
    """Run a powershell command line on the users machine"""

    print(f"{GREEN}>{RESET} {command_line}")    
    command_line_expanded = (f"({command_line}) ; (pwd).Path")
    result = subprocess.run(['powershell', '-Command', command_line_expanded], capture_output=True, text=True, shell=True)

    # Change current working directory since commands might change it (cd ..) etc
    lines = result.stdout.rstrip().splitlines()
    os.chdir(lines[-1])

    # Strip out the (pwd).Path and keep the other output from the call
    command_line_output = '\n'.join(lines[:-1])

    print(command_line_output)
    
    if result.stderr:
        print(f"{RED}{result.stderr}{RESET}")
        
    return result.stderr if result.stderr else command_line_output

