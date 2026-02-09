"""
Clerk JWT Token Verification Module

Handles verification of Clerk-issued JWT tokens for API authentication.
Fetches Clerk's JWKS (JSON Web Key Set) and validates tokens using RS256.

Ported from Court Vision's backend/core/clerk_auth.py.
"""

import jwt
import requests
from functools import lru_cache
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from sqlmate.backend.utils.constants import CLERK_JWKS_URL, CLERK_SECRET_KEY

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_clerk_jwks() -> dict:
    """Fetch and cache Clerk's JWKS public keys."""
    if not CLERK_JWKS_URL:
        raise HTTPException(
            status_code=500,
            detail="CLERK_JWKS_URL environment variable not configured"
        )

    try:
        response = requests.get(CLERK_JWKS_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch Clerk JWKS: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch authentication keys"
        )


def get_public_key_for_token(token: str):
    """Get the RSA public key matching the token's 'kid' header."""
    jwks = get_clerk_jwks()

    try:   
        unverified_header = jwt.get_unverified_header(token)
    except jwt.exceptions.DecodeError as e:
        print(f"Failed to decode token header: {e}")
        raise HTTPException(status_code=401, detail="Invalid token format")

    kid = unverified_header.get('kid')
    if not kid:
        raise HTTPException(status_code=401, detail="Token missing key ID")

    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Key not found - clear cache and retry once (handles key rotation)
    get_clerk_jwks.cache_clear()
    jwks = get_clerk_jwks()

    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    raise HTTPException(status_code=401, detail="Unable to find appropriate signing key")


def fetch_clerk_user(clerk_user_id: str) -> Optional[dict]:
    """
    Fetch user details from Clerk's Backend API.

    Returns dict with clerk_user_id, email, first_name, last_name, or None on failure.
    """
    if not CLERK_SECRET_KEY:
        print("Warning: CLERK_SECRET_KEY not configured, cannot fetch user details")
        return None

    try:
        response = requests.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={
                "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        response.raise_for_status()
        user_data = response.json()

        email = None
        email_addresses = user_data.get('email_addresses', [])
        primary_email_id = user_data.get('primary_email_address_id')
        for email_obj in email_addresses:
            if email_obj.get('id') == primary_email_id:
                email = email_obj.get('email_address')
                break
        if not email and email_addresses:
            email = email_addresses[0].get('email_address')

        return {
            "clerk_user_id": user_data.get('id'),
            "email": email,
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
        }

    except requests.RequestException as e:
        print(f"Failed to fetch user from Clerk API: {e}")
        return None


def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify a Clerk JWT token and return the payload.

    Use as a FastAPI dependency:
        @router.get('/protected')
        def protected_route(current_user: dict = Depends(verify_clerk_token)):
            ...

    Returns dict with 'clerk_user_id', 'email', and token claims.
    """
    token = credentials.credentials

    try:
        public_key = get_public_key_for_token(token)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_iss": False,
            }
        )

        clerk_user_id = payload.get("sub")
        email = payload.get("email")

        # If email not in JWT, fetch from Clerk's API
        if not email and clerk_user_id:
            clerk_user = fetch_clerk_user(clerk_user_id)
            if clerk_user:
                email = clerk_user.get("email")

        return {
            "clerk_user_id": clerk_user_id,
            "email": email,
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Wrapper around verify_clerk_token for backward compatibility."""
    return verify_clerk_token(credentials)


def clear_jwks_cache():
    """Clear the JWKS cache (e.g. after key rotation)."""
    get_clerk_jwks.cache_clear()
