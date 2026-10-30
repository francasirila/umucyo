from sqlalchemy.orm import Session, joinedload

from models.payment_report import PaymentReport


class PaymentReportRepository:
    """All database queries for payment reports."""

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(PaymentReport).options(joinedload(PaymentReport.farmer))

    def list_for_cooperative(self, cooperative_id, status=None, limit=50, offset=0):
        query = self._base_query().filter(PaymentReport.cooperative_id == cooperative_id)
        if status:
            query = query.filter(PaymentReport.status == status)
        return query.order_by(PaymentReport.created_at.desc()).limit(limit).offset(offset).all()

    def get(self, payment_report_id, cooperative_id):
        """A report, only if it belongs to the given cooperative."""
        return (
            self._base_query()
            .filter(
                PaymentReport.payment_report_id == payment_report_id,
                PaymentReport.cooperative_id == cooperative_id,
            )
            .first()
        )

    def update_status(self, report, status):
        report.status = status
        self.db.commit()
        self.db.refresh(report)
        return report
