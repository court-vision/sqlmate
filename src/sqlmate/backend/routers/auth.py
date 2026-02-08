from sqlmate.backend.utils.clerk_auth import verify_clerk_token
from sqlmate.backend.classes.http import StatusResponse

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

router = APIRouter()

# ================================= AUTH ENDPOINTS =================================

class UserInfoResponse(BaseModel):
    details: StatusResponse
    clerk_user_id: str | None = None
    email: str | None = None

@router.get('/me', response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
def me(current_user: dict = Depends(verify_clerk_token)) -> UserInfoResponse:
    return UserInfoResponse(
        details=StatusResponse(
            status="success",
            message="User info retrieved successfully",
            code=status.HTTP_200_OK
        ),
        clerk_user_id=current_user.get("clerk_user_id"),
        email=current_user.get("email"),
    )
