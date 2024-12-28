from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class SettingsResponse(BaseModel):
    history_size: Optional[int] = Field(
        None,
        description="The number of chat messages stored in the interchange between user and Cortex. A higher value makes Cortex remember more but implies higher usage cost."    
    )
    shell: Optional[Literal['powershell', 'bash']] = Field (None, description="The users chosen shell terminal.")
    model: Optional[Literal['gpt-4o', 'gpt-4o-mini', 'chatgpt-4o-latest', 'o1', 'o1-mini', 'o1-preview',]] = Field (None, description="The AI model engine that Cortex will use.")
    explain: Optional[bool] = Field(None, description="If set to True, Cortex will explain commands after execution. If set to False, less usage cost and faster response times.")
    autocomplete: Optional[bool] = Field(None, description="If set to true, autocompletes with files found in the current users directory. Only used in RUN mode.")

class RequestResponse(BaseModel):
    message: str = Field(
        ..., 
        description="A response to the users message"
    )
    settings: Optional[SettingsResponse] = Field(
        None, description="Populated when the user wants to change any of the settings related to Cortex."
    )
    command_lines: Optional[List[str]] = Field(
        None, 
        description=f"A list of shell commands to execute if you deem they should be run (destructive operations require prior approval)"
    )

class ResultResponse(BaseModel):
    message: str = Field(
        ..., 
        description="A brief explanation of the output of the recently ran command by you. On any errors, try to guide the user to a solution."
    )

    