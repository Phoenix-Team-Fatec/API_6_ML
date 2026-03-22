from pydantic import BaseModel, Field

class CodeChangeRequest(BaseModel):
    user_request: str = Field(..., description="Requested business rule change")

class CodeEditProposal(BaseModel):
    target_file: str = Field(..., description="Relative path to the file to change, e.g. src/agent/rules/base_algorithm.py")
    change_summary: str = Field(..., description="Short summary of the change made")
    updated_code: str = Field(..., description="The COMPLETE file content after the change. Must be the entire file from the first line to the last, not a snippet or partial code.")