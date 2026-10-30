from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from services.ussd_service import UssdService

router = APIRouter(prefix="/api/v1/ussd", tags=["USSD"])


@router.post("/", response_class=PlainTextResponse)
@router.post("", response_class=PlainTextResponse, include_in_schema=False)
def ussd_callback(
    phoneNumber: str = Form(...),
    text: str = Form(""),
    sessionId: str = Form(""),
    serviceCode: str = Form(""),
    db: Session = Depends(get_db),
):
    return PlainTextResponse(UssdService(db).process_request(phoneNumber, text))
