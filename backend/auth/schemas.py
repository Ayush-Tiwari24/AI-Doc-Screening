import uuid

from pydantic import BaseModel, ConfigDict

from db.models import UserRole


class UserRegister(BaseModel):
    name: str
    badge_id: str
    password: str
    role: UserRole
    checkpoint_id: uuid.UUID | None = None


class UserLogin(BaseModel):
    badge_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    badge_id: str
    role: UserRole
    checkpoint_id: uuid.UUID | None