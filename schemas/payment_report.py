import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

ReportStatus = Literal["pending", "resolved", "rejected"]


class PaymentReportOut(BaseModel):
    payment_report_id: uuid.UUID
    farmer_id: uuid.UUID
    farmer_name: str
    farmer_phone: str | None
    report_type: str
    reported_month_start: date
    reported_month_label: str
    description: str
    status: str
    confirmation_sms_sent: bool
    created_at: datetime


class PaymentReportStatusUpdate(BaseModel):
    status: ReportStatus
