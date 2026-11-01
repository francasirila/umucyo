from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from services.ussd_service import UssdService

router = APIRouter(prefix="/ussd", tags=["USSD"])


@router.post("/", response_class=PlainTextResponse)
def ussd_callback(
    phoneNumber: str = Form(...),
    text: str = Form(""),
    sessionId: str = Form(""),
    serviceCode: str = Form(""),
    db: Session = Depends(get_db),
):
    return PlainTextResponse(UssdService(db).process_request(phoneNumber, text))
