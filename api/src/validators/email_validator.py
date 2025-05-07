from src.configs.validation_config import register_validator
from pydantic import BaseModel, EmailStr

class EmailValidator(BaseModel):
    @classmethod
    def validate_email(cls, email: EmailStr) -> bool:
        return '@' in email

def register_validators(config):
    register_validator('email', EmailValidator.validate_email)