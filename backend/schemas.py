from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, List


# ---------- RESPONSE MODELS ----------

class GenerateEmailData(BaseModel):
    recipient: Optional[str]
    cc: Optional[str]
    subject: Optional[str]
    body: Optional[str]


class GenerateEmailResponse(BaseModel):
    status: str
    data: GenerateEmailData


class SendEmailResponse(BaseModel):
    status: str
    recipient: List[EmailStr]
    cc: Optional[List[EmailStr]]
    subject: str


class RegenerateResponse(BaseModel):
    status: str
    body: str


# ---------- REQUEST MODELS ----------

class SendEmailRequest(BaseModel):
    recipient: List[EmailStr]
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    cc: Optional[List[EmailStr]] = None


class RegenerateRequest(BaseModel):
    original_body: str = Field(..., min_length=1)
    instruction: Optional[str] = None

# ---------- ERROR MODEL ----------

class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Any] = None