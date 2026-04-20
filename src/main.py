from sanic import Sanic
from sanic.response import json
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.admin import admin_bp
from src.routes.webhook import webhook_bp
from src.core.database import Base, engine

# Create tables if they don't exist (for development)
Base.metadata.create_all(bind=engine)

app = Sanic("PaymentApp")

# Enable Sanic-EXT for automatic OpenAPI documentation
app.config.OAS = True
app.config.OAS_UI = "swagger"  # or "redoc" for ReDoc UI

# Register blueprints
app.blueprint(auth_bp)
app.blueprint(user_bp)
app.blueprint(admin_bp)
app.blueprint(webhook_bp)

@app.route("/")
async def hello(request):
    """Main endpoint - shows welcome message and API info"""
    return json({
        "message": "Welcome to the Payment API",
        "documentation": {
            "openapi_ui": "http://localhost:8000/docs",
            "api_docs_json": "http://localhost:8000/api-docs",
            "api_reference": [
                "POST /auth/login - Login and get JWT token",
                "GET /user/profile - Get user profile (requires auth)",
                "GET /user/accounts - Get user accounts (requires auth)",
                "GET /user/payments - Get user payments (requires auth)",
                "POST /admin/login - Admin login",
                "GET /admin/users - Get all users (admin only)",
                "POST /admin/users - Create user (admin only)",
                "PUT /admin/users/{id} - Update user (admin only)",
                "DELETE /admin/users/{id} - Delete user (admin only)",
                "POST /webhook/payment - Process payment webhook (signature required)"
            ]
        }
    })

# Custom API documentation endpoint (reliable fallback)
@app.get("/api-docs")
async def api_docs_custom(request):
    """Custom API documentation endpoint with all endpoints listed"""
    return json({
        "title": "Payment API Documentation",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "POST /auth/login": {
                    "description": "Authenticate user and get JWT token",
                    "body": {"email": "string", "password": "string"},
                    "response": {"access_token": "string", "token_type": "bearer"}
                }
            },
            "user": {
                "GET /user/profile": {
                    "description": "Get current user profile",
                    "auth": "Bearer <token>"
                },
                "GET /user/accounts": {
                    "description": "Get user accounts and balances",
                    "auth": "Bearer <token>"
                },
                "GET /user/payments": {
                    "description": "Get user payment history",
                    "auth": "Bearer <token>"
                }
            },
            "admin": {
                "POST /admin/login": {
                    "description": "Authenticate admin",
                    "body": {"email": "string", "password": "string"}
                },
                "GET /admin/users": {
                    "description": "Get all users (admin only)",
                    "auth": "Bearer <admin_token>"
                },
                "POST /admin/users": {
                    "description": "Create new user (admin only)",
                    "body": {"email": "string", "password": "string", "full_name": "string"}
                }
            },
            "webhook": {
                "POST /webhook/payment": {
                    "description": "Process payment webhook",
                    "headers": {"X-Signature": "SHA256 signature"},
                    "body": {"user_id": "integer", "transaction_id": "string", "amount": "number"}
                }
            }
        }
    })

@app.route("/health")
async def health_check(request):
    """Health check endpoint"""
    return json({"status": "healthy", "service": "Payment API"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)