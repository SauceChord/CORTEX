import configparser
from pydantic import BaseModel

class Settings(BaseModel):
    history_size: int
    shell: str
    model: str
    explain: bool

parser = configparser.ConfigParser()
with open("config.ini") as fd:
    parser.read_file(fd)

settings = Settings(**parser["Settings"])