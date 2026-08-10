from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from config import (
    APP_ENV,
    FRONTEND_URL,
    JWT_SECRET_KEY,
    OLLAMA_MODEL,
)

from services.workflow_runner import run_workflow
from services.workflow_store import _seed_default_workflow_if_needed

from routes.google_auth import (
    router as google_auth_router,
)
from routes.credentials import (
    router as credentials_router,
)
from routes.whatsapp_webhook import (
    router as whatsapp_webhook_router,
)
from routes.workflow import (
    router as workflow_router,
)
from routes.setup import (
    router as setup_router,
)
from routes.auth import (
    router as auth_router,
)
from routes.business import (
    router as business_router,
)
from database import engine, init_db


print("APP_ENV:", APP_ENV)
print("OLLAMA_MODEL:", OLLAMA_MODEL)


app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    if os.getenv("RAILWAY_PUBLIC_DOMAIN") and not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set in production (Railway environment)."
        )

    init_db()
    _seed_default_workflow_if_needed()


# Google OAuth routes
app.include_router(google_auth_router)

# Credentials routes
app.include_router(credentials_router)

# Meta WhatsApp webhook routes
app.include_router(whatsapp_webhook_router)

# Saved workflow routes (for WhatsApp triggers)
app.include_router(workflow_router)

# Production diagnostics
app.include_router(setup_router)

# User authentication and business onboarding
app.include_router(auth_router)
app.include_router(business_router)


allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://mini-n8n-gilt.vercel.app",
]

if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Mini n8n backend is working"
    }


@app.get("/health")
def health():
    """Public liveness check — reports DB dialect only, never connection secrets."""
    dialect = engine.dialect.name
    database_url_configured = bool(os.getenv("DATABASE_URL"))

    return {
        "ok": True,
        "database": dialect,
        "database_url_configured": database_url_configured,
        "persistent": dialect != "sqlite",
    }


@app.post("/run-workflow")
def execute_workflow(workflow: dict):
    try:
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        result = run_workflow(
            nodes=nodes,
            edges=edges,
        )

        return {
            "success": True,
            **result,
        }

    except Exception as error:
        print("Workflow error:", error)

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )