import logging
import re
from datetime import date

from sqlalchemy.orm import Session

from models.enums import PaymentStatus
from models.farmer import Farmer
from models.payment_transaction import PaymentTransaction
from models.produce_record import ProduceRecord
from services.sms_service import SmsService
from services.translations import (
    BILINGUAL,
    DEFAULT_LANGUAGE,
    LANGUAGE_MENU,
    LANGUAGES,
    format_date,
    month_label,
    tr,
)

logger = logging.getLogger(__name__)


class UssdService:
    def __init__(self, db: Session):
        self.db = db
        self.sms_service = SmsService(db)

    def _clean_phone(self, phone: str) -> str:
        return re.sub(r"\D", "", phone or "")[-9:]

    @staticmethod
    def _month_range(offset: int) -> tuple[date, date]:
        today = date.today()
        year, month = today.year, today.month - offset

        while month < 1:
            month += 12
            year -= 1

        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        return start, end

    def _month_label(
        self,
        offset: int,
        lang: str = DEFAULT_LANGUAGE,
        short: bool = False,
    ) -> str:
        return month_label(lang, self._month_range(offset)[0], short)

    def _month_menu(self, title: str, lang: str = DEFAULT_LANGUAGE) -> str:
        lines = [f"{i + 1}. {self._month_label(i, lang)}" for i in range(3)]
        return f"CON {title}\n" + "\n".join(lines)

    def _month_status(self, farmer: Farmer, offset: int):
        start, end = self._month_range(offset)

        payments = (
            self.db.query(PaymentTransaction)
            .join(
                ProduceRecord,
                ProduceRecord.produce_record_id == PaymentTransaction.produce_record_id,
            )
            .filter(
                PaymentTransaction.farmer_id == farmer.user_id,
                ProduceRecord.recorded_at >= start,
                ProduceRecord.recorded_at < end,
            )
            .all()
        )

        if not payments:
            return None

        weight = sum(payment.quantity for payment in payments)
        paid = all(payment.status == PaymentStatus.paid for payment in payments)

        paid_on = None

        if paid:
            dates = [
                payment_date for payment_date in (getattr(payment, "payment_date", None) for payment in payments) if payment_date
            ]
            paid_on = max(dates) if dates else None

        return weight, paid, paid_on

    @staticmethod
    def _status_text(lang: str, paid: bool, paid_on, with_year: bool) -> str:
        if not paid:
            return tr(lang, "unpaid")

        if paid_on:
            return tr(
                lang,
                "paid_on",
                date=format_date(lang, paid_on, with_year),
            )

        return tr(lang, "paid")

    def _submit_report(
        self,
        farmer: Farmer,
        description: str,
        sms_text: str,
    ) -> bool:
        logger.info("%s", description)

        try:
            return bool(
                self.sms_service.send_custom_sms(
                    farmer.phone_number,
                    sms_text,
                )
            )
        except Exception:
            logger.exception(
                "Confirmation SMS failed for farmer %s",
                farmer.user_id,
            )
            return False

    def process_request(self, phone_number: str, text: str) -> str:
        try:
            return self._process(phone_number, text or "")
        except Exception:
            logger.exception("USSD request failed")
            self.db.rollback()
            return BILINGUAL["error"]

    def _process(self, phone_number: str, text: str) -> str:
        clean_number = self._clean_phone(phone_number)

        if len(clean_number) < 9:
            return BILINGUAL["invalid_phone"]

        farmer = self.db.query(Farmer).filter(Farmer.phone_number.like(f"%{clean_number}")).first()

        if not farmer:
            return BILINGUAL["not_registered"]

        text = text.strip()

        if text == "":
            return LANGUAGE_MENU

        parts = text.split("*")
        lang = LANGUAGES.get(parts[0])

        if lang is None:
            return BILINGUAL["invalid_choice"]

        parts = parts[1:]

        if not parts:
            return tr(lang, "main_menu")

        if parts[0] == "1":
            return self._handle_payment_history(farmer, parts, lang)

        if parts[0] == "2":
            return self._handle_report_issue(farmer, parts, lang)

        return tr(lang, "invalid_choice")

    def _handle_payment_history(
        self,
        farmer: Farmer,
        parts: list[str],
        lang: str,
    ) -> str:
        if parts == ["1"]:
            return tr(lang, "history_menu")

        if parts == ["1", "1"]:
            status = self._month_status(farmer, 0)
            label = self._month_label(0, lang)

            if status is None:
                return tr(lang, "history_none_month", month=label)

            weight, paid, paid_on = status

            return tr(
                lang,
                "history_month",
                month=label,
                weight=f"{weight:,.1f}",
                status=self._status_text(lang, paid, paid_on, True),
            )

        if parts == ["1", "2"]:
            lines = []

            for offset in (2, 1, 0):
                label = self._month_label(offset, lang, short=True)
                status = self._month_status(farmer, offset)

                if status is None:
                    lines.append(tr(lang, "line_no_records", month=label))
                else:
                    weight, paid, paid_on = status

                    lines.append(
                        tr(
                            lang,
                            "line_record",
                            month=label,
                            weight=f"{weight:,.1f}",
                            status=self._status_text(
                                lang,
                                paid,
                                paid_on,
                                False,
                            ),
                        )
                    )

            return tr(lang, "history_three_header") + "\n" + "\n".join(lines)

        return tr(lang, "invalid_history_choice")

    def _handle_report_issue(
        self,
        farmer: Farmer,
        parts: list[str],
        lang: str,
    ) -> str:
        if parts == ["2"]:
            return tr(lang, "report_menu")

        if len(parts) < 2:
            return tr(lang, "invalid_report_choice")

        kind = parts[1]

        if kind not in ("1", "2"):
            return tr(lang, "invalid_report_choice")

        if len(parts) == 2:
            title = tr(
                lang,
                "ask_month_less" if kind == "1" else "ask_month_unpaid",
            )
            return self._month_menu(title, lang)

        if len(parts) != 3 or parts[2] not in ("1", "2", "3"):
            return tr(lang, "invalid_month")

        offset = int(parts[2]) - 1
        english_label = self._month_label(offset, "en")
        label = self._month_label(offset, lang)

        who = f"Farmer {farmer.first_name} ({farmer.phone_number})"

        if kind == "1":
            description = f"USSD PAYMENT ISSUE: {who} reports LESS PAYMENT for {english_label}."
            sms_text = tr(
                lang,
                "sms_less",
                name=farmer.first_name,
                month=label,
            )
        else:
            description = f"USSD PAYMENT ISSUE: {who} reports NOT PAID AT ALL for {english_label}."
            sms_text = tr(
                lang,
                "sms_unpaid",
                name=farmer.first_name,
                month=label,
            )

        sent = self._submit_report(
            farmer=farmer,
            description=description,
            sms_text=sms_text,
        )

        return tr(lang, "report_sent" if sent else "report_failed")
