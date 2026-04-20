from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic.exceptions import Unauthorized
from src.models.user import User
from src.models.account import Account
from src.models.payment import Payment
from src.core.database import SessionLocal
from src.core.security import verify_token

user_bp = Blueprint("user", url_prefix="/user")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_user_token(request: Request):
    """Verify JWT token from Authorization header and return user data."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise Unauthorized("Missing or invalid Authorization header")
    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        # Ensure the token is for a non-admin user
        if payload.get("is_admin"):
            raise Unauthorized("Admin token not allowed for user endpoints")
        return payload
    except Exception as e:
        raise Unauthorized(str(e))

@user_bp.get("/profile")
async def get_profile(request: Request):
    """Get current user's profile data."""
    payload = verify_user_token(request)
    user_id = int(payload["sub"])
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Unauthorized("User not found")
        return json({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        })
    finally:
        db.close()

@user_bp.get("/accounts")
async def get_accounts(request: Request):
    """Get list of user's accounts and balances."""
    payload = verify_user_token(request)
    user_id = int(payload["sub"])
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(Account.user_id == user_id).all()
        result = []
        for account in accounts:
            result.append({
                "id": account.id,
                "balance": float(account.balance)
            })
        return json(result)
    finally:
        db.close()

@user_bp.get("/payments")
async def get_payments(request: Request):
    """Get list of user's payments."""
    payload = verify_user_token(request)
    user_id = int(payload["sub"])
    db = SessionLocal()
    try:
        # Join with account to get payments for user's accounts
        payments = db.query(Payment).join(Account).filter(Account.user_id == user_id).all()
        result = []
        for payment in payments:
            result.append({
                "id": payment.id,
                "transaction_id": payment.transaction_id,
                "amount": float(payment.amount),
                "created_at": payment.created_at.isoformat() if payment.created_at else None
            })
        return json(result)
    finally:
        db.close()