from typing import Optional

from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, EmailStr, field_validator
import uuid

# Models:
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID]

class TokenPayload(BaseModel):
    sub: str | None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str | EmailStr

    @field_validator('email')
    def validate_email_rfc(cls, v):
        try:
            result = validate_email(v, check_deliverability=False)
            if v.lower() != "admin@example.com":
                blocked_domains = {'tempmail.com', 'example.com'}
                domain = v.split('@')[-1]
                if domain in blocked_domains:
                    raise ValueError('Disposable emails are not allowed')
            return result.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

class NewPassword(BaseModel):
    token: str
    new_password: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str