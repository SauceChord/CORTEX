from typing import Optional, List
from pydantic import BaseModel, Field
from cortex_lib.config import settings

class RequestResponse(BaseModel):
    message: str = Field(
        ..., 
        description="A response to the users message"
    )
    command_lines: Optional[List[str]] = Field(
        None, 
        description=f"A list of {settings.shell} commands to execute if you deem they should be run (destructive operations require prior approval)"
    )

class ResultResponse(BaseModel):
    message: str = Field(
        ..., 
        description="A brief explanation of the output of the recently ran command by you. On any errors, try to guide the user to a solution."
    )