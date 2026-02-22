from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
import re
from datetime import datetime

class SignUpModel(BaseModel):
    email: str
    username: str = Field(max_length=32)
    last_name: str = Field(max_length=32)
    first_name: str = Field(max_length=32)
    password: str = Field(max_length=64)
    confirm_password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Must contain at least one special character.")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class SignInModel(BaseModel):
    email: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str | None = "bearer"

class UserModel(BaseModel):
    id: UUID = Field(alias="_id")
    username: str
    email: str
    display_name: str | None = Field(alias="displayName")
    avatar_url: str | None = Field(alias="avatarUrl")
    bio: str | None
    phone: str | None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }