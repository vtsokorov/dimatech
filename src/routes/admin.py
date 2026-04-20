from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic.exceptions import Unauthorized
from src.models.user import User
from src.models.account import Account
from src.core.database import SessionLocal
from src.core.security import verify_token

admin_bp = Blueprint("admin", url_prefix="/admin")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin_token(request: Request):
    """Verify JWT token from Authorization header and return admin data."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise Unauthorized("Missing or invalid Authorization header")
    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        # Ensure the token is for an admin user
        if not payload.get("is_admin"):
            raise Unauthorized("Admin token required")
        return payload
    except Exception as e:
        raise Unauthorized(str(e))

@admin_bp.post("/login")
async def admin_login(request: Request):
    """
    Login endpoint for admins (same as user login, but we can keep separate for clarity).
    Expects JSON: { "email": "admin@example.com", "password": "password" }
    Returns: { "access_token": "token", "token_type": "bearer" }
    """
    # Reuse the same login logic as user login, but we can keep it here for admin-specific if needed.
    # For simplicity, we'll redirect to the auth login endpoint, but since we are in a different blueprint,
    # we'll just copy the logic or call the auth function. Let's copy for simplicity.
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return json({"error": "Email and password are required"}, status=400)

    email = data["email"]
    password = data["password"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_admin:
            raise Unauthorized("Invalid email or password or not an admin")
        # Verify password
        from src.core.security import verify_password
        if not verify_password(password, user.password_hash):
            raise Unauthorized("Invalid email or password")

        # Create access token
        import datetime
        from src.core.security import create_access_token
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

@admin_bp.get("/profile")
async def get_admin_profile(request: Request):
    """Get current admin's profile data."""
    payload = verify_admin_token(request)
    user_id = int(payload["sub"])
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Unauthorized("Admin not found")
        return json({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        })
    finally:
        db.close()

@admin_bp.get("/users")
async def get_users_with_accounts(request: Request):
    """Get list of users and their accounts with balances."""
    verify_admin_token(request)  # Ensure admin
    db = SessionLocal()
    try:
        users = db.query(User).all()
        result = []
        for user in users:
            accounts = db.query(Account).filter(Account.user_id == user.id).all()
            accounts_data = [{"id": acc.id, "balance": float(acc.balance)} for acc in accounts]
            result.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin,
                "accounts": accounts_data
            })
        return json(result)
    finally:
        db.close()

@admin_bp.post("/users")
async def create_user(request: Request):
    """Create a new user (admin only)."""
    verify_admin_token(request)
    data = request.json
    if not data or "email" not in data or "password" not in data or "full_name" not in data:
        return json({"error": "Email, password, and full_name are required"}, status=400)

    email = data["email"]
    password = data["password"]
    full_name = data["full_name"]
    is_admin = data.get("is_admin", False)

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return json({"error": "User with this email already exists"}, status=400)

        # Hash password
        from src.core.security import hash_password
        password_hash = hash_password(password)

        new_user = User(email=email, password_hash=password_hash, full_name=full_name, is_admin=is_admin)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return json({
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "is_admin": new_user.is_admin
        }), 201
    finally:
        db.close()

@admin_bp.put("/users/{user_id}")
async def update_user(request: Request, user_id: int):
    """Update an existing user (admin only)."""
    verify_admin_token(request)
    data = request.json
    if not data:
        return json({"error": "No data provided"}, status=400)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json({"error": "User not found"}, status=404)

        if "email" in data:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(User.email == data["email"]).first()
            if existing_user and existing_user.id != user_id:
                return json({"error": "Email already in use"}, status=400)
            user.email = data["email"]
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "is_admin" in data:
            user.is_admin = data["is_admin"]
        if "password" in data:
            from src.core.security import hash_password
            user.password_hash = hash_password(data["password"])

        db.commit()
        db.refresh(user)

        return json({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        })
    finally:
        db.close()

@admin_bp.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: int):
    """Delete a user (admin only)."""
    verify_admin_token(request)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json({"error": "User not found"}, status=404)

        db.delete(user)
        db.commit()

        return json({"message": "User deleted successfully"})
    finally:
        db.close()