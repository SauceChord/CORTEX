import configparser
import os
from pydantic import BaseModel


class Settings(BaseModel):
    history_size: int
    shell: str
    model: str
    explain: bool
    autocomplete: bool


# Capture the absolute path of the current working directory
current_dir = os.path.abspath(os.getcwd())
config_file_path = os.path.join(current_dir, "config.ini")

def create_default_config():
    if not os.path.exists(config_file_path):
        print("No config.ini found, creating default...")
        parser["Settings"] = {
            "history_size": 10,
            "shell": "powershell",
            "model": "gpt-4o-mini",
            "explain": "False",
            "autocomplete": "False",
        }
        with open(config_file_path, "w") as configfile:
            parser.write(configfile)


parser = configparser.ConfigParser()

# Ensure the default configuration is created on import
create_default_config()

with open(config_file_path) as fd:
    parser.read_file(fd)

settings = Settings(**parser["Settings"])


def settings_hint():
    return f"""Current Cortex setting are:
    history_size: {settings.history_size}
    shell: {settings.shell}
    model: {settings.model}
    explain: {settings.explain}
    autocomplete: {settings.autocomplete}"""


def get_settings():
    return settings


def set_settings(new_settings):
    parser["Settings"] = {
        "history_size": new_settings.history_size,
        "shell": new_settings.shell,
        "model": new_settings.model,
        "explain": new_settings.explain,
        "autocomplete": new_settings.autocomplete,
    }

    # Write the updated configuration back to the file
    with open(config_file_path, "w") as configfile:
        parser.write(configfile)
