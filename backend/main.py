from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import (
    APP_ENV,
    FRONTEND_URL,
    OLLAMA_MODEL,
)

from services.workflow_runner import run_workflow

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


print("APP_ENV:", APP_ENV)
print("OLLAMA_MODEL:", OLLAMA_MODEL)


app = FastAPI()


# Google OAuth routes
app.include_router(google_auth_router)

# Credentials routes
app.include_router(credentials_router)

# Meta WhatsApp webhook routes
app.include_router(whatsapp_webhook_router)

# Saved workflow routes (for WhatsApp triggers)
app.include_router(workflow_router)


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