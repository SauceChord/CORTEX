import subprocess

def run_powershell(command_line):
    """Run a powershell command line on the users machine"""
    result = subprocess.run(['powershell', '-Command', command_line], capture_output=True, text=True)
    print(f"> {command_line}")
    print(result.stdout)
    return result.stdout
