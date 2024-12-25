import subprocess
import os

def run_powershell(command_line):
    """Run a powershell command line on the users machine"""

    command_line_expanded = (f"({command_line}) ; (pwd).Path")
    result = subprocess.run(['powershell', '-Command', command_line_expanded], capture_output=True, text=True, shell=True)

    # Change current working directory since commands might change it (cd ..) etc
    lines = result.stdout.rstrip().splitlines()
    os.chdir(lines[-1])

    # Strip out the (pwd).Path and keep the other output from the call
    command_line_output = '\n'.join(lines[:-1])

    print(f"> {command_line}")
    print(command_line_output)
        
    return command_line_output

