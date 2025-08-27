from .constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS
from datetime import datetime, timedelta
from typing import Tuple, Dict
import bcrypt
import jwt

def hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
	return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: Dict) -> str:
	to_encode = data.copy()
	to_encode.update({"exp": datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)})
	if SECRET_KEY is None:
		raise ValueError("SECRET_KEY cannot be None")
	return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_token(authorization: str | None) -> str:
	if not authorization:
		return ""
	if not authorization.startswith("Bearer "):
		return ""
	return authorization.split(" ")[1]

# Return (user_id, error_msg)
def check_user(token: str | None) -> Tuple[str, str, str]:
	if not token:
		return "", "", "Token is missing"
	
	if not token.startswith("Bearer "):
		return "", "", "Invalid token format"
	
	token = token.split(" ")[1]
	try:
		payload = verify_and_decode_token(token)
		user_id = payload.get("id")
		username = payload.get("username")
		if not user_id or not username:
			return "", "", "Invalid token payload"
		return user_id, username, ""
	except Exception as _:
		return "", "", "Invalid token"

def verify_and_decode_token(token: str) -> dict:
		try:
			if SECRET_KEY is None:
				raise ValueError("SECRET_KEY cannot be None")
			payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
			return payload
		except jwt.ExpiredSignatureError:
			raise Exception("Token has expired")
		except jwt.InvalidTokenError:
			raise Exception("Invalid token")