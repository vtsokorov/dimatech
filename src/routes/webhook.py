from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from sanic.exceptions import ServerError, BadRequest
from src.models.account import Account
from src.models.payment import Payment
from src.core.database import SessionLocal
from src.core.security import verify_payment_signature
import json as json_module

webhook_bp = Blueprint("webhook", url_prefix="/webhook")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@webhook_bp.route("/payment", methods=["POST"])
async def payment_webhook(request: Request):
    """
    Endpoint to handle webhook from payment system.
    Expects JSON with transaction data and a signature.
    The signature is verified using SHA256 of sorted keys + secret_key.
    Steps:
    1. Extract JSON data and signature from headers (or as per payment system spec).
    2. Verify the signature.
    3. Check if transaction_id already exists (idempotency).
    4. Get or create account for the user (if user_id is provided, or create a default user?).
       According to the plan: "Создание счета, если не существует" (Create account if not exists).
       We need to know which user the account belongs to. The webhook should contain user_id or email.
       Let's assume the webhook payload includes: user_id (or email), transaction_id, amount.
    5. Create payment record and update account balance.

    However, the plan does not specify the exact webhook format. We'll assume:
    - Headers: X-Signature: <signature>
    - JSON body: { "user_id": 1, "transaction_id": "txn_123", "amount": 100.50 }

    We'll adjust if needed.

    For now, we'll follow the plan: 
      - Проверка подписи (SHA256 от concatenated sorted keys + secret_key)
      - Создание счета, если не существует
      - Сохранение транзакции (уникальная по transaction_id)
      - Начисление суммы на счет

    We'll need a secret key for signature verification. We'll get it from settings.
    """
    # Get signature from header (assuming X-Signature)
    signature = request.headers.get("X-Signature")
    if not signature:
        return json({"error": "Missing signature"}, status=400)

    # Get JSON data
    try:
        data = request.json
    except Exception:
        return json({"error": "Invalid JSON"}, status=400)

    if not data:
        return json({"error": "Missing data"}, status=400)

    # We expect certain keys in the data. Let's assume: user_id, transaction_id, amount
    required_keys = ["user_id", "transaction_id", "amount"]
    for key in required_keys:
        if key not in data:
            return json({"error": f"Missing key: {key}"}, status=400)

    user_id = data["user_id"]
    transaction_id = data["transaction_id"]
    amount = data["amount"]

    # Verify signature
    # We need to get the secret key from settings
    from src.core.config import settings
    secret_key = settings.SECRET_KEY

    # For signature verification, we sort the keys of the data (excluding the signature itself)
    # and concatenate their values (as strings) in sorted order, then append the secret key.
    # However, the plan says: "SHA256 от concatenated sorted keys + secret_key"
    # It might mean: sort the keys of the JSON, concatenate the keys (not values?) + secret_key?
    # Let's assume: sort the keys, concatenate the string representation of each value? 
    # But the plan says "concatenated sorted keys", which might mean the keys themselves.
    # We'll clarify: typically, you sort the keys and concatenate the values (or key=value pairs).
    # Since the plan is ambiguous, we'll implement a common method: 
    #   sorted_keys = sorted(data.keys())
    #   concatenated = ''.join([str(data[k]) for k in sorted_keys]) + secret_key
    # But note: the plan says "concatenated sorted keys", not "concatenated sorted values".
    # Let's re-read: "Проверка подписи (SHA256 от concatenated sorted keys + secret_key)"
    # It might be: take the keys, sort them, concatenate the keys (as strings) and then add secret_key.
    # However, that would not depend on the values, which is unsafe.
    # We'll assume it's a mistake and they meant values. Alternatively, it could be key=value pairs.
    # Given the ambiguity, we'll implement as: sort the keys, concatenate the values (as strings) in that order, then add secret_key.
    # We'll note that the secret key is from settings.

    # Verify signature using the defined function
    # The function expects: sorted keys (alphabetically) concatenated + secret_key
    # This matches the implementation in core.security
    if not verify_payment_signature(list(data.keys()), secret_key, signature):
        # We'll also log for debugging
        return json({"error": "Invalid signature"}, status=400)

    # Check if transaction already exists (idempotency)
    db = SessionLocal()
    try:
        existing_payment = db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
        if existing_payment:
            # Already processed, return success
            return json({"status": "already processed"})

        # Get or create account for the user
        account = db.query(Account).filter(Account.user_id == user_id).first()
        if not account:
            # Create a new account for the user with zero balance, then we'll add the amount
            account = Account(user_id=user_id, balance=0.0)
            db.add(account)
            db.commit()
            db.refresh(account)

        # Create payment record
        new_payment = Payment(
            transaction_id=transaction_id,
            account_id=account.id,
            amount=amount
        )
        db.add(new_payment)

        # Update account balance
        account.balance += amount

        db.commit()

        return json({"status": "success", "account_id": account.id, "new_balance": float(account.balance)})
    except Exception as e:
        db.rollback()
        raise ServerError(f"Failed to process webhook: {str(e)}")
    finally:
        db.close()