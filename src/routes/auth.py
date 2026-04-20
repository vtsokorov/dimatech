from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic.exceptions import Unauthorized
from src.models.user import User
from src.core.database import SessionLocal
from src.core.security import verify_password, create_access_token
import datetime

auth_bp = Blueprint("auth", url_prefix="/auth")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@auth_bp.post("/login")
async def login(request: Request):
    """
    Login endpoint for both users and admins.
    Expects JSON: { "email": "user@example.com", "password": "password" }
    Returns: { "access_token": "token", "token_type": "bearer" }
    """
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return json({"error": "Email and password are required"}, status=400)

    email = data["email"]
    password = data["password"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise Unauthorized("Invalid email or password")

        # Create access token
        access_token_expires = datetime.timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "is_admin": user.is_admin},
            expires_delta=access_token_expires
        )

        return json({
            "access_token": access_token,
            "token_type": "bearer"
        })
    finally:
        db.close()