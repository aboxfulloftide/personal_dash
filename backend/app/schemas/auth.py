from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request body for login endpoint."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Response containing only access token."""

    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for logout."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
