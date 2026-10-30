from datetime import date

DEFAULT_LANGUAGE = "en"

LANGUAGES = {"1": "rw", "2": "en"}

LANGUAGE_MENU = "CON Hitamo ururimi / Choose language:\n1. Kinyarwanda\n2. English"

BILINGUAL = {
    "invalid_phone": "END Invalid phone number.\nNumero ya telefone ntiyemewe.",
    "not_registered": (
        "END You are not registered. Please visit your cooperative to register.\n"
        "Ntiwanditswe. Jya kuri koperative yawe kwiyandikisha."
    ),
    "invalid_choice": "END Invalid choice. Please try again.\nAmahitamo siyo. Ongera ugerageze.",
    "error": (
        "END Sorry, something went wrong. Please try again later.\nMutwihanganire, habaye ikibazo. Ongera ugerageze nyuma."
    ),
}

MONTHS = {
    "en": {
        "long": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "short": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    },
    "rw": {
        "long": [
            "Mutarama",
            "Gashyantare",
            "Werurwe",
            "Mata",
            "Gicurasi",
            "Kamena",
            "Nyakanga",
            "Kanama",
            "Nzeri",
            "Ukwakira",
            "Ugushyingo",
            "Ukuboza",
        ],
        "short": ["Mut", "Gas", "Wer", "Mat", "Gic", "Kam", "Nya", "Kan", "Nze", "Ukw", "Ugu", "Uku"],
    },
}

STRINGS = {
    "en": {
        "main_menu": "CON Welcome to Umucyo. Please select:\n1. Payment History\n2. Report a Payment Issue",
        "history_menu": "CON Payment History:\n1. This month\n2. Last 3 months",
        "history_none_month": "END {month}: no records.",
        "history_month": "END {month}\nWeight: {weight} kg\nStatus: {status}",
        "history_three_header": "END Last 3 months:",
        "line_no_records": "{month}: no records",
        "line_record": "{month}: {weight}kg, {status}",
        "paid": "Paid",
        "paid_on": "Paid on {date}",
        "unpaid": "Unpaid",
        "report_menu": "CON Report a Payment Issue:\n1. Less payment\n2. Not paid at all",
        "ask_month_less": "Which month was the payment less?",
        "ask_month_unpaid": "Which month were you not paid?",
        "report_sent": "END Your report was sent successfully.",
        "report_failed": "END Sorry, we could not send your report. Please try again later.",
        "invalid_choice": "END Invalid choice. Please try again.",
        "invalid_history_choice": "END Invalid choice in Payment History.",
        "invalid_report_choice": "END Invalid choice in Reporting.",
        "invalid_month": "END Invalid month. Please dial again and choose 1, 2 or 3.",
        "sms_less": "Dear {name}, your report of less payment for {month} was sent successfully to the cooperative.",
        "sms_unpaid": "Dear {name}, your report that you were not paid for {month} was sent successfully to the cooperative.",
        "sms_delivery": "Dear {name}, {weight} kg of produce was delivered at {point}, {coop} on {date}. Amount to be paid: RWF {amount}.",
        "fallback_point": "the collection point",
        "fallback_coop": "the cooperative",
    },
    "rw": {
        "main_menu": "CON Murakaza neza kuri Umucyo. Hitamo:\n1. Amateka y'ubwishyu\n2. Tanga ikibazo cy'ubwishyu",
        "history_menu": "CON Amateka y'ubwishyu:\n1. Uku kwezi\n2. Amezi 3 ashize",
        "history_none_month": "END {month}: Nta makuru ahari.",
        "history_month": "END {month}\nIbiro: {weight} kg\nUko bimeze: {status}",
        "history_three_header": "END Amezi 3 ashize:",
        "line_no_records": "{month}: nta makuru",
        "line_record": "{month}: {weight}kg, {status}",
        "paid": "Wishyuwe",
        "paid_on": "Wishyuwe ku wa {date}",
        "unpaid": "Ntabwo wishyuwe",
        "report_menu": "CON Tanga ikibazo cy'ubwishyu:\n1. Nishyuwe make\n2. Sinishyuwe na gato",
        "ask_month_less": "Ni ukuhe kwezi wishyuwe make?",
        "ask_month_unpaid": "Ni ukuhe kwezi utishyuwe?",
        "report_sent": "END Ikibazo cyawe cyoherejwe neza.",
        "report_failed": "END Mutwihanganire, ntitwabashije kohereza ikibazo cyawe. Ongera ugerageze nyuma.",
        "invalid_choice": "END Amahitamo siyo. Ongera ugerageze.",
        "invalid_history_choice": "END Amahitamo siyo mu mateka y'ubwishyu.",
        "invalid_report_choice": "END Amahitamo siyo mu gutanga ikibazo.",
        "invalid_month": "END Ukwezi si ko. Ongera uhamagare, ukande 1, 2 cyangwa 3.",
        "sms_less": "Muraho {name}, ikibazo cyawe cy'ubwishyu bwa make mu kwezi kwa {month} cyoherejwe neza kuri koperative.",
        "sms_unpaid": "Muraho {name}, ikibazo cyawe cyo kutishyurwa mu kwezi kwa {month} cyoherejwe neza kuri koperative.",
        "sms_delivery": "Muraho {name}, ibiro {weight} by'icyayi byakiriwe kuri {point}, {coop} ku wa {date}. Amafaranga uzishyurwa: RWF {amount}.",
        "fallback_point": "ahakirirwa icyayi",
        "fallback_coop": "koperative",
    },
}


def tr(lang: str, key: str, **values) -> str:
    """Look a sentence up in the farmer's language (English if the language is unknown)."""
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANGUAGE]
    return table[key].format(**values)


def month_label(lang: str, day: date, short: bool = False) -> str:
    """'Oct 2026' / 'Ukwakira 2026', or just 'Oct' / 'Ukw' when short."""
    names = (MONTHS.get(lang) or MONTHS[DEFAULT_LANGUAGE])["short" if short else "long"]
    name = names[day.month - 1]
    return name if short else f"{name} {day.year}"


def format_date(lang: str, day, with_year: bool = True) -> str:
    """'20 Oct 2026' / '20 Ukwakira 2026'; without the year the short month name is used."""
    names = (MONTHS.get(lang) or MONTHS[DEFAULT_LANGUAGE])["long" if with_year else "short"]
    text = f"{day.day:02d} {names[day.month - 1]}"
    return f"{text} {day.year}" if with_year else text
