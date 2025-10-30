from pydantic import BaseModel, EmailStr, ConfigDict

class PasswordResetRequest(BaseModel):
    email: EmailStr
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class PasswordResetValidateResponse(BaseModel):
    valid: bool

class PasswordResetRequestResponse(BaseModel):
    reset_link: str

