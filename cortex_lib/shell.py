import subprocess
import os

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

def run_bash(cmd):
    return run_shell(cmd, shell="bash", switch="-c", path="pwd", useShell=False)

def run_ps(cmd):
    return run_shell(cmd, shell="powershell", switch="-Command", path="(pwd).Path", useShell=True)

def run_shell(cmd, shell, switch, path, useShell):
    """Run a shell command line on the users machine"""
    try:
        print(f"{GREEN}>{RESET} {cmd}")    
        cmd_pwd = (f"({cmd}) ; {path}")
        cmd_pwd_output = subprocess.run([shell, switch, cmd_pwd], capture_output=True, text=True, shell=useShell)

        # Change current working directory since commands might change it (cd ..) etc
        # This is so CORTEX understands navigation in the directories
        cmd_pwd_lines = cmd_pwd_output.stdout.rstrip().splitlines()
        os.chdir(cmd_pwd_lines[-1])

        # Strip out the current directory and keep the other output from the call
        # With other words, the desired output of the cmd call.
        cmd_output = '\n'.join(cmd_pwd_lines[:-1])

        print(cmd_output)

        if cmd_pwd_output.stderr:
            print(f"{RED}{cmd_pwd_output.stderr}{RESET}")
            
        return cmd_pwd_output.stderr if cmd_pwd_output.stderr else cmd_output
    except Exception as e:
        print(f"{RED}EXECUTION ERROR:{RESET} {e}")
        return f"Execution error: {e}"
