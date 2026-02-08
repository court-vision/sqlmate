from sqlmate.backend.utils.clerk_auth import verify_clerk_token
from sqlmate.backend.utils.db import session_scope
from sqlmate.backend.utils.user_provisioning import get_or_create_sqlmate_user
from sqlmate.backend.classes.http import StatusResponse

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

router = APIRouter()

# ================================= AUTH ENDPOINTS =================================

class UserInfoResponse(BaseModel):
    details: StatusResponse
    clerk_user_id: str | None = None
    email: str | None = None
    display_name: str | None = None

@router.get('/me', response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
def me(current_user: dict = Depends(verify_clerk_token)) -> UserInfoResponse:
    clerk_user_id = current_user.get("clerk_user_id")
    email = current_user.get("email")

    # Ensure the user exists in our local clerk_users table
    with session_scope("sqlmate") as session:
        get_or_create_sqlmate_user(session, clerk_user_id, email)

    return UserInfoResponse(
        details=StatusResponse(
            status="success",
            message="User info retrieved successfully",
            code=status.HTTP_200_OK
        ),
        clerk_user_id=clerk_user_id,
        email=email,
    )
