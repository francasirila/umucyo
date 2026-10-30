from repositories.payment_report import PaymentReportRepository
from schemas.payment_report import PaymentReportOut


class PaymentReportService:
    """What the cooperative dashboard needs from the reports farmers send over USSD."""

    def __init__(self, db=None, *, reports=None):
        self.reports = reports if reports is not None else PaymentReportRepository(db)

    @staticmethod
    def to_output(report) -> PaymentReportOut:
        farmer = report.farmer
        return PaymentReportOut(
            payment_report_id=report.payment_report_id,
            farmer_id=report.farmer_id,
            farmer_name=f"{farmer.first_name} {farmer.last_name}".strip(),
            farmer_phone=farmer.phone_number,
            report_type=report.report_type,
            reported_month_start=report.reported_month_start,
            reported_month_label=report.reported_month_label,
            description=report.description,
            status=report.status,
            confirmation_sms_sent=report.confirmation_sms_sent,
            created_at=report.created_at,
        )

    def list_reports(self, cooperative_id, status=None, limit=50, offset=0):
        rows = self.reports.list_for_cooperative(cooperative_id, status, limit, offset)
        return [self.to_output(row) for row in rows]

    def get_report(self, payment_report_id, cooperative_id):
        report = self.reports.get(payment_report_id, cooperative_id)
        return self.to_output(report) if report else None

    def update_status(self, payment_report_id, cooperative_id, status):
        report = self.reports.get(payment_report_id, cooperative_id)
        if report is None:
            return None
        return self.to_output(self.reports.update_status(report, status))
