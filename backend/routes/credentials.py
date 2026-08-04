from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.credentials_service import (
    save_credentials,
    load_credentials,
)


router = APIRouter()


@router.post("/credentials")
def create_credentials(data: dict):
    try:
        save_credentials(data)

        return {
            "success": True,
            "message": "Credentials saved securely.",
        }

    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )


@router.get("/credentials")
def get_credentials():
    try:
        credentials = load_credentials()

        return {
            "success": True,
            "credentials": credentials,
        }

    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )