import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.payment_report import PaymentReportOut, PaymentReportStatusUpdate, ReportStatus
from services.payment_report import PaymentReportService

router = APIRouter(prefix="/api/v1/payment-reports", tags=["Payment Reports"])


def get_payment_report_service(db: Annotated[Session, Depends(get_db)]) -> PaymentReportService:
    return PaymentReportService(db)


ServiceDep = Annotated[PaymentReportService, Depends(get_payment_report_service)]
CooperativeQuery = Annotated[uuid.UUID, Query(description="Which cooperative's reports")]


@router.get("", response_model=list[PaymentReportOut])
def list_payment_reports(
    service: ServiceDep,
    cooperative_id: CooperativeQuery,
    status: Annotated[ReportStatus | None, Query(description="Only reports in this state")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Payment problems farmers reported over USSD, newest first."""
    return service.list_reports(cooperative_id, status, limit, offset)


@router.get("/{payment_report_id}", response_model=PaymentReportOut)
def get_payment_report(
    payment_report_id: uuid.UUID, service: ServiceDep, cooperative_id: CooperativeQuery
):
    report = service.get_report(payment_report_id, cooperative_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Payment report not found")
    return report


@router.patch("/{payment_report_id}/status", response_model=PaymentReportOut)
def update_payment_report_status(
    payment_report_id: uuid.UUID,
    body: PaymentReportStatusUpdate,
    service: ServiceDep,
    cooperative_id: CooperativeQuery,
):
    """Mark a report as pending, resolved or rejected."""
    report = service.update_status(payment_report_id, cooperative_id, body.status)
    if report is None:
        raise HTTPException(status_code=404, detail="Payment report not found")
    return report
